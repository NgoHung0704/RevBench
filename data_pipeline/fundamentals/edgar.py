"""SEC EDGAR XBRL client (docs/PLAN.md 1.3, docs/DATA_SOURCES.md §3).

EDGAR is the official, free source for quarterly fundamentals, and the only one
that records *when* each number was filed — which is what makes point-in-time
correctness possible.

Point-in-time rule: companyfacts gives the filing date without a time of day,
so a filing made on day D gets available_at = D+1 00:00 UTC. Assuming intraday
availability would peek ahead; we accept up to one day of lag instead.
"""

import os
from functools import cached_property

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# SEC requires a descriptive User-Agent with a contact address (10 req/s limit).
DEFAULT_USER_AGENT = "RevBench student research project ngohung.hsgs19@gmail.com"

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# Companies tag the same economic concept differently; first candidate with data wins.
METRIC_TAGS: dict[str, list[tuple[str, str, str]]] = {
    "revenue": [
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax", "USD"),
        ("us-gaap", "Revenues", "USD"),
        ("us-gaap", "SalesRevenueNet", "USD"),
    ],
    "net_income": [("us-gaap", "NetIncomeLoss", "USD")],
    "eps_diluted": [("us-gaap", "EarningsPerShareDiluted", "USD/shares")],
}

_COLUMNS = [
    "ticker", "metric", "period_start", "period_end", "value",
    "unit", "form", "fy", "fp", "accn", "filed",
]


def normalize_facts(raw: dict, ticker: str) -> pd.DataFrame:
    """companyfacts JSON -> one row per (metric, period, filing). Pure, testable."""
    facts = raw.get("facts", {})
    rows: list[dict] = []
    for metric, candidates in METRIC_TAGS.items():
        for namespace, tag, unit in candidates:
            entries = facts.get(namespace, {}).get(tag, {}).get("units", {}).get(unit, [])
            usable = [e for e in entries if e.get("form", "").startswith(("10-K", "10-Q"))]
            if not usable:
                continue
            rows.extend(
                {
                    "ticker": ticker,
                    "metric": metric,
                    "period_start": entry.get("start"),
                    "period_end": entry["end"],
                    "value": float(entry["val"]),
                    "unit": unit,
                    "form": entry["form"],
                    "fy": entry.get("fy"),
                    "fp": entry.get("fp"),
                    "accn": entry["accn"],
                    "filed": entry["filed"],
                }
                for entry in usable
            )
            break  # first candidate tag with data wins
    df = pd.DataFrame(rows, columns=_COLUMNS)
    if df.empty:
        df["available_at"] = pd.Series(dtype="datetime64[ns]")
        return df
    for col in ("period_start", "period_end", "filed"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["available_at"] = df["filed"] + pd.Timedelta(days=1)
    df["fy"] = df["fy"].astype("Int64")
    # include period_start: a 10-Q reports both a 3-month and a year-to-date value
    # for the same concept (same period_end + accn), differing only in start.
    df = df.drop_duplicates(
        subset=["metric", "period_start", "period_end", "accn"], keep="last"
    )
    return df.sort_values(["metric", "period_end"]).reset_index(drop=True)


class EdgarClient:
    def __init__(self, user_agent: str | None = None):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            user_agent or os.environ.get("EDGAR_USER_AGENT") or DEFAULT_USER_AGENT
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def _get_json(self, url: str) -> dict:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    @cached_property
    def _cik_by_ticker(self) -> dict[str, int]:
        data = self._get_json(TICKERS_URL)
        return {row["ticker"].upper(): int(row["cik_str"]) for row in data.values()}

    def cik_for(self, ticker: str) -> int:
        try:
            return self._cik_by_ticker[ticker.upper()]
        except KeyError:
            raise ValueError(f"no CIK found on EDGAR for {ticker}") from None

    def quarterly_facts(self, ticker: str) -> pd.DataFrame:
        raw = self._get_json(FACTS_URL.format(cik=self.cik_for(ticker)))
        return normalize_facts(raw, ticker)
