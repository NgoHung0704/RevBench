"""Wikipedia pageviews adapter (docs/DECISIONS.md D8, DATA_SOURCES.md §5).

An attention proxy with the same research basis as Google Trends (Moat et al.
2013 linked Wikipedia views to market moves), but via the *official* Wikimedia
REST API — free, reliable, no bot-blocking, daily history back to 2015. This is
why it's our working alt-data source where the unofficial Trends endpoint 429s
(docs/REVISIT.md R14). Every value is point-in-time: day D's views become
available on D+1.
"""

from datetime import date, datetime, timedelta
from urllib.parse import quote

import requests
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from .base import AltDataPoint, AltDataProvider, ProviderRateLimited

API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia.org/all-access/all-agents/{article}/daily/{start}/{end}"
)
USER_AGENT = "RevBench student research (ngohung.hsgs19@gmail.com)"

# Each ticker -> its English Wikipedia article title.
WIKI_ARTICLE: dict[str, str] = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft", "NVDA": "Nvidia", "GOOGL": "Google",
    "AMZN": "Amazon (company)", "META": "Meta Platforms", "TSLA": "Tesla, Inc.",
    "JPM": "JPMorgan Chase", "V": "Visa Inc.", "MA": "Mastercard",
    "KO": "The Coca-Cola Company", "PG": "Procter & Gamble", "JNJ": "Johnson & Johnson",
    "XOM": "ExxonMobil", "DIS": "The Walt Disney Company",
}


class WikipediaProvider(AltDataProvider):
    source = "wikipedia"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=20),
        retry=retry_if_not_exception_type(ProviderRateLimited),
        reraise=True,
    )
    def fetch_series(self, ticker: str, start: date, end: date) -> list[AltDataPoint]:
        article = WIKI_ARTICLE.get(ticker.upper())
        if article is None:
            raise ValueError(f"no Wikipedia article mapped for {ticker}")
        url = API.format(
            article=quote(article.replace(" ", "_"), safe=""),
            start=start.strftime("%Y%m%d"),
            end=end.strftime("%Y%m%d"),
        )
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if resp.status_code == 429:
            raise ProviderRateLimited("Wikipedia pageviews 429")
        if resp.status_code == 404:
            return []  # no data for this article/range
        resp.raise_for_status()
        return self._to_points(resp.json().get("items", []), ticker)

    @staticmethod
    def _to_points(items: list[dict], ticker: str) -> list[AltDataPoint]:
        points: list[AltDataPoint] = []
        for item in items:
            ts = item.get("timestamp", "")  # "YYYYMMDD00"
            if len(ts) < 8 or "views" not in item:
                continue
            day = datetime.strptime(ts[:8], "%Y%m%d").date()
            points.append(
                AltDataPoint(
                    source="wikipedia",
                    ticker=ticker,
                    date=day,
                    value=float(item["views"]),
                    # day D's pageviews are published on D+1 -> no lookahead
                    available_at=datetime(day.year, day.month, day.day) + timedelta(days=1),
                )
            )
        return points
