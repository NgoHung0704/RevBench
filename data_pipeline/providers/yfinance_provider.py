"""yfinance adapter — primary dev/backtest source (docs/DECISIONS.md D1).

Unofficial Yahoo endpoint: expect occasional breakage. This class stays thin;
the canonical schema lives in base.py so a replacement adapter is cheap.
"""

from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import PRICE_COLUMNS, PriceProvider, validate_prices

_RENAME = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


class YFinanceProvider(PriceProvider):
    name = "yfinance"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def fetch_daily(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        raw = yf.Ticker(ticker).history(
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),  # yfinance end is exclusive
            interval="1d",
            auto_adjust=False,
            actions=False,
        )
        return self._normalize(raw, ticker)

    @staticmethod
    def _normalize(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
        if raw.empty:
            raise ValueError(f"yfinance returned no data for {ticker}")
        df = raw.rename(columns=_RENAME)
        if "adj_close" not in df.columns:
            # auto-adjusted feed: close is already the adjusted series
            df["adj_close"] = df["close"]
        df = df[PRICE_COLUMNS].copy()
        idx = pd.to_datetime(df.index)
        if idx.tz is not None:
            idx = idx.tz_localize(None)
        df.index = pd.DatetimeIndex(idx.normalize(), name="date")
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return validate_prices(df, ticker)
