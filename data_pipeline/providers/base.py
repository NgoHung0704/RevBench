"""Provider interfaces (docs/DECISIONS.md D1).

Free data sources break; every source sits behind an interface so we swap
adapters, not logic (CLAUDE.md conventions).
"""

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

# Canonical daily-bar schema every PriceProvider must return.
PRICE_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


class PriceProvider(ABC):
    """Daily OHLCV source for one ticker at a time."""

    name: str

    @abstractmethod
    def fetch_daily(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Return daily bars for `ticker` over [start, end] inclusive.

        Contract: naive DatetimeIndex named "date" (exchange dates, midnight),
        columns exactly PRICE_COLUMNS, ascending, no duplicate dates,
        `adj_close` adjusted for splits and dividends.
        """


def validate_prices(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Enforce the PriceProvider contract; raise ValueError listing every violation."""
    problems: list[str] = []

    missing = [c for c in PRICE_COLUMNS if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")
    if not isinstance(df.index, pd.DatetimeIndex):
        problems.append("index is not a DatetimeIndex")
    else:
        if df.index.tz is not None:
            problems.append("index must be timezone-naive")
        if not df.index.is_monotonic_increasing:
            problems.append("index not sorted ascending")
        if df.index.has_duplicates:
            problems.append("duplicate dates in index")

    if not missing:
        prices = df[["open", "high", "low", "close", "adj_close"]]
        if (prices.dropna() <= 0).any().any():
            problems.append("non-positive prices found")
        if (df["volume"].dropna() < 0).any():
            problems.append("negative volume found")
        hl = df[["high", "low"]].dropna()
        if (hl["high"] < hl["low"]).any():
            problems.append("high < low on some rows")

    if problems:
        raise ValueError(f"invalid price data for {ticker}: " + "; ".join(problems))
    return df[PRICE_COLUMNS]
