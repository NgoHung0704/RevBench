"""News provider interface + canonical item (docs/DECISIONS.md D7).

Same swap-the-adapter rule as prices: every news source implements NewsProvider
and returns NewsItem — downstream code never sees source-specific shapes.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import sha1

from pydantic import BaseModel


class NewsItem(BaseModel):
    id: str
    ticker: str
    title: str
    summary: str = ""
    url: str
    source: str
    published_at: datetime  # naive UTC
    available_at: datetime  # naive UTC — when we could have known it (point-in-time rule)


def item_id(url: str) -> str:
    """Stable article id derived from the URL (dedup key across fetches)."""
    return sha1(url.encode("utf-8")).hexdigest()[:16]


class ProviderRateLimited(Exception):
    """The source is rate-limiting our IP — abandon this provider's whole pass.

    Retrying other tickers against the same limiter only extends the cooldown;
    the next scheduled run picks up what was missed (providers overlap their
    time windows and the store dedups by URL).
    """


class NewsProvider(ABC):
    name: str

    @abstractmethod
    def fetch_for_ticker(self, ticker: str) -> list[NewsItem]:
        """Recent articles tagged to `ticker`, newest last not guaranteed — store sorts."""
