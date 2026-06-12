"""Price panels + labels for research/backtests (docs/PLAN.md Phase 2).

Timing convention (anti-lookahead, see docs/FINANCE_PRIMER.md §1.3):
- Features at date t use data through close(t) only.
- The trade executes at close(t+1) — the signal exists only in the evening of t,
  so trading at the close we just observed would be a cheat.
- The label is the H-day return from close(t+1) to close(t+1+H).
"""

from __future__ import annotations

import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH, PriceStore
from data_pipeline.universe import HORIZON_DAYS, TICKERS


def load_frames(
    db_path=DEFAULT_DB_PATH,
    tickers: tuple[str, ...] = TICKERS,
    source: str = "yfinance",
) -> dict[str, pd.DataFrame]:
    """Full daily bars per ticker, DatetimeIndex ascending."""
    frames: dict[str, pd.DataFrame] = {}
    with PriceStore(db_path) as store:
        for ticker in tickers:
            df = store.load_daily(ticker, source=source)
            if df.empty:
                continue
            df.index = pd.to_datetime(df.index)
            frames[ticker] = df.sort_index()
    return frames


def returns_panel(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Daily simple returns, wide (date x ticker), from adjusted closes."""
    closes = pd.DataFrame({t: f["adj_close"] for t, f in frames.items()}).sort_index()
    return closes.pct_change()


def make_labels(adj_close: pd.Series, horizon: int = HORIZON_DAYS) -> pd.Series:
    """1.0 if the H-day return from close(t+1) to close(t+1+H) is positive.

    NaN where the forward window runs past the end of the data (last H+1 rows) —
    those rows are usable for prediction but not for training/evaluation.
    """
    exec_price = adj_close.shift(-1)
    settle_price = adj_close.shift(-(1 + horizon))
    forward = settle_price / exec_price - 1.0
    label = (forward > 0).astype(float)
    label[forward.isna()] = float("nan")
    return label
