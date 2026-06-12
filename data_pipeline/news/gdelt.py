"""GDELT DOC 2.0 adapter (docs/DECISIONS.md D7) — broad-coverage news.

Queries by company name, so precision is lower than per-ticker feeds; the
sentiment agent downstream is the noise filter. available_at = GDELT `seendate`
(when the article entered the public index).
"""

import time
from datetime import datetime

import requests
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from ..universe import STOCK_BY_TICKER
from .base import NewsItem, NewsProvider, ProviderRateLimited, item_id

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
USER_AGENT = "RevBench student research project"

# GDELT throttles harder than its documented ~1 req/5 s (rolling per-IP window);
# 15 s spacing measured reliable. Nightly batch pace, so latency is irrelevant —
# and the 3-day timespan overlap means a ticker that still 429s tonight is
# picked up by tomorrow's run (dedup by URL makes the overlap free).
MIN_INTERVAL_S = 15.0


class GDELTProvider(NewsProvider):
    name = "gdelt"

    def __init__(self, timespan: str = "3d", max_records: int = 50):
        # 3-day window overlaps daily runs so a missed run self-heals (dedup by URL)
        self.timespan = timespan
        self.max_records = max_records
        self._last_request = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=20, max=120),
        # 429 means our IP is cooling down — retrying makes it worse, fail fast instead
        retry=retry_if_not_exception_type(ProviderRateLimited),
        reraise=True,
    )
    def fetch_for_ticker(self, ticker: str) -> list[NewsItem]:
        stock = STOCK_BY_TICKER.get(ticker.upper())
        if stock is None:
            raise ValueError(f"{ticker} is not in the universe")
        query = f'"{stock.name}" (stock OR shares OR earnings) sourcelang:english'
        self._throttle()
        try:
            response = requests.get(
                GDELT_URL,
                params={
                    "query": query,
                    "mode": "ArtList",
                    "maxrecords": self.max_records,
                    "timespan": self.timespan,
                    "format": "json",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
        finally:
            self._last_request = time.monotonic()
        if response.status_code == 429:
            raise ProviderRateLimited("GDELT returned 429 — IP-level cooldown")
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return self._to_items(articles, ticker)

    @staticmethod
    def _to_items(articles: list[dict], ticker: str) -> list[NewsItem]:
        items: list[NewsItem] = []
        for article in articles:
            url = article.get("url", "")
            if not url:
                continue
            try:
                seen = datetime.strptime(article.get("seendate", ""), "%Y%m%dT%H%M%SZ")
            except ValueError:
                continue  # no usable timestamp -> cannot place point-in-time -> skip
            items.append(
                NewsItem(
                    id=item_id(url),
                    ticker=ticker,
                    title=article.get("title", "").strip(),
                    url=url,
                    source="gdelt",
                    published_at=seen,
                    available_at=seen,
                )
            )
        return items
