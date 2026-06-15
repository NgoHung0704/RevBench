"""Google Trends adapter (docs/DECISIONS.md D8, DATA_SOURCES.md §5).

Search interest as an attention/demand proxy. Unlike news, Trends serves *years*
of history, so its feature can actually be backtested against the price window
(news could not — see docs/REVISIT.md R2). Unofficial endpoint: rate-limits hard
(429), so we throttle and fail the pass fast, like GDELT.

Each ticker maps to a representative search term (a flagship product or the
brand). The mapping is config — tune it and let the Information Coefficient say
which terms actually carry signal.
"""

import time
from datetime import date, datetime, timedelta

import pandas as pd
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from .base import AltDataPoint, AltDataProvider, ProviderRateLimited

# Representative search term per ticker (tunable; weak ones get filtered by IC).
TRENDS_KEYWORD: dict[str, str] = {
    "AAPL": "iPhone", "MSFT": "Microsoft", "NVDA": "Nvidia", "GOOGL": "Google",
    "AMZN": "Amazon", "META": "Facebook", "TSLA": "Tesla", "JPM": "Chase Bank",
    "V": "Visa card", "MA": "Mastercard", "KO": "Coca Cola", "PG": "Tide detergent",
    "JNJ": "Johnson & Johnson", "XOM": "Exxon", "DIS": "Disney",
}

# Google Trends weekly data lags ~2 days; a value for a week-end isn't usable
# until after it's published.
AVAILABILITY_LAG_DAYS = 2
MIN_INTERVAL_S = 3.0  # be polite to the unofficial endpoint


class GoogleTrendsProvider(AltDataProvider):
    source = "google_trends"

    def __init__(self):
        self._last_request = 0.0
        self._client = None

    def _pytrends(self):
        if self._client is None:
            from pytrends.request import TrendReq  # imported lazily (heavy, optional)

            self._client = TrendReq(hl="en-US", tz=0)
        return self._client

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=10, max=60),
        retry=retry_if_not_exception_type(ProviderRateLimited),
        reraise=True,
    )
    def fetch_series(self, ticker: str, start: date, end: date) -> list[AltDataPoint]:
        keyword = TRENDS_KEYWORD.get(ticker.upper())
        if keyword is None:
            raise ValueError(f"no Trends keyword mapped for {ticker}")
        client = self._pytrends()
        self._throttle()
        try:
            client.build_payload([keyword], timeframe=f"{start.isoformat()} {end.isoformat()}")
            df = client.interest_over_time()
        except Exception as exc:  # pytrends raises a generic error on 429
            if "429" in str(exc) or "rate" in str(exc).lower():
                raise ProviderRateLimited("Google Trends 429") from exc
            raise
        finally:
            self._last_request = time.monotonic()
        return self._to_points(df, ticker, keyword)

    @staticmethod
    def _to_points(df: pd.DataFrame, ticker: str, keyword: str) -> list[AltDataPoint]:
        if df is None or df.empty or keyword not in df.columns:
            return []
        points: list[AltDataPoint] = []
        for ts, row in df.iterrows():
            if row.get("isPartial", False):
                continue  # the current, still-incomplete period
            period = pd.Timestamp(ts).date()
            points.append(
                AltDataPoint(
                    source="google_trends",
                    ticker=ticker,
                    date=period,
                    value=float(row[keyword]),
                    available_at=datetime(period.year, period.month, period.day)
                    + timedelta(days=AVAILABILITY_LAG_DAYS),
                )
            )
        return points
