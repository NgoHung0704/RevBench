"""Yahoo Finance per-ticker RSS adapter (docs/DECISIONS.md D7).

Per-ticker feeds give ticker tagging for free. General market feeds (CNBC, GDELT)
come later and will need keyword-based entity linking.
"""

from datetime import UTC, datetime

import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import NewsItem, NewsProvider, item_id

FEED_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"


class YahooRSSProvider(NewsProvider):
    name = "yahoo_rss"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def fetch_for_ticker(self, ticker: str) -> list[NewsItem]:
        feed = feedparser.parse(FEED_URL.format(ticker=ticker))
        if feed.bozo and not feed.entries:
            raise ValueError(f"failed to fetch Yahoo RSS for {ticker}: {feed.bozo_exception}")
        return self._to_items(feed, ticker)

    @staticmethod
    def _to_items(feed, ticker: str) -> list[NewsItem]:
        now = datetime.now(UTC).replace(tzinfo=None)
        items: list[NewsItem] = []
        for entry in feed.entries:
            url = getattr(entry, "link", "")
            if not url:
                continue
            parsed = getattr(entry, "published_parsed", None)
            # feedparser normalizes published_parsed to UTC
            published = datetime(*parsed[:6]) if parsed else now
            items.append(
                NewsItem(
                    id=item_id(url),
                    ticker=ticker,
                    title=getattr(entry, "title", "").strip(),
                    summary=getattr(entry, "summary", "").strip(),
                    url=url,
                    source="yahoo_rss",
                    published_at=published,
                    # RSS is near-realtime: the item was publicly known at publish time
                    available_at=published,
                )
            )
        return items
