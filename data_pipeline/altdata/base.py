"""Alternative-data provider interface (docs/DECISIONS.md D8).

Same swap-the-adapter rule as prices/news: each alt-data source (Google Trends,
Wikipedia pageviews, …) implements AltDataProvider and returns AltDataPoint, so
downstream features never see source-specific shapes. Every point carries an
`available_at` so a backtest only reads what it could have known.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime

from pydantic import BaseModel


class AltDataPoint(BaseModel):
    source: str
    ticker: str
    date: date  # the period the value describes (e.g., a week-ending date)
    value: float
    available_at: datetime  # naive UTC — when we could have known it


class ProviderRateLimited(Exception):
    """The source is rate-limiting us — abandon this pass; the next run retries."""


class AltDataProvider(ABC):
    source: str

    @abstractmethod
    def fetch_series(self, ticker: str, start: date, end: date) -> list[AltDataPoint]:
        """Historical series for one ticker over [start, end]."""
