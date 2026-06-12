from datetime import date, timedelta

import pandas as pd
import pytest

from data_pipeline.providers.base import PRICE_COLUMNS, validate_prices
from data_pipeline.providers.yfinance_provider import YFinanceProvider


def fake_yahoo_frame() -> pd.DataFrame:
    """Mimic yfinance output: capitalized columns, tz-aware New York index."""
    idx = pd.DatetimeIndex(
        pd.to_datetime(["2026-01-06", "2026-01-05", "2026-01-06"])
    ).tz_localize("America/New_York")
    return pd.DataFrame(
        {
            "Open": [102.0, 100.0, 102.0],
            "High": [103.0, 101.0, 103.0],
            "Low": [101.0, 99.0, 101.0],
            "Close": [102.5, 100.5, 102.5],
            "Adj Close": [102.0, 100.0, 102.0],
            "Volume": [2_000_000, 1_000_000, 2_000_000],
        },
        index=idx,
    )


def test_normalize_schema_sort_dedup():
    df = YFinanceProvider._normalize(fake_yahoo_frame(), "AAPL")
    assert list(df.columns) == PRICE_COLUMNS
    assert df.index.name == "date"
    assert df.index.tz is None
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    assert len(df) == 2  # duplicate 2026-01-06 collapsed


def test_normalize_fills_adj_close_when_auto_adjusted():
    raw = fake_yahoo_frame().drop(columns=["Adj Close"])
    df = YFinanceProvider._normalize(raw, "AAPL")
    assert (df["adj_close"] == df["close"]).all()


def test_normalize_rejects_empty():
    with pytest.raises(ValueError, match="no data"):
        YFinanceProvider._normalize(pd.DataFrame(), "AAPL")


def test_validate_rejects_high_below_low():
    df = YFinanceProvider._normalize(fake_yahoo_frame(), "AAPL").copy()
    df.loc[df.index[0], "high"] = 1.0  # below low
    with pytest.raises(ValueError, match="high < low"):
        validate_prices(df, "AAPL")


@pytest.mark.integration
def test_real_fetch_aapl_30_days():
    end = date.today()
    df = YFinanceProvider().fetch_daily("AAPL", end - timedelta(days=30), end)
    assert len(df) >= 15  # ~20 trading days in 30 calendar days
    assert list(df.columns) == PRICE_COLUMNS
