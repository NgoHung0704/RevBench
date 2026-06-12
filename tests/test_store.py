import pandas as pd

from data_pipeline.store import PriceStore


def make_bars(dates: list[str]) -> pd.DataFrame:
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    n = len(idx)
    return pd.DataFrame(
        {
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.5] * n,
            "adj_close": [100.5] * n,
            "volume": [1_000_000] * n,
        },
        index=idx,
    )


def test_roundtrip(tmp_path):
    with PriceStore(tmp_path / "t.duckdb") as store:
        n = store.upsert_daily("AAPL", make_bars(["2026-01-05", "2026-01-06"]), "test")
        assert n == 2
        out = store.load_daily("AAPL")
        assert len(out) == 2
        assert list(out["close"]) == [100.5, 100.5]


def test_upsert_is_idempotent(tmp_path):
    bars = make_bars(["2026-01-05", "2026-01-06"])
    with PriceStore(tmp_path / "t.duckdb") as store:
        store.upsert_daily("AAPL", bars, "test")
        store.upsert_daily("AAPL", bars, "test")  # same rows again
        assert len(store.load_daily("AAPL")) == 2


def test_available_at_is_after_market_close(tmp_path):
    with PriceStore(tmp_path / "t.duckdb") as store:
        store.upsert_daily("AAPL", make_bars(["2026-01-05"]), "test")
        row = store.load_daily("AAPL").iloc[0]
        # bar for Jan 5 becomes known at 21:00 UTC that day, never at midnight
        assert row["available_at"] == pd.Timestamp("2026-01-05 21:00:00")


def test_sources_kept_separate(tmp_path):
    bars = make_bars(["2026-01-05"])
    with PriceStore(tmp_path / "t.duckdb") as store:
        store.upsert_daily("AAPL", bars, "yfinance")
        store.upsert_daily("AAPL", bars, "tiingo")
        assert len(store.load_daily("AAPL")) == 2
        assert len(store.load_daily("AAPL", source="tiingo")) == 1
