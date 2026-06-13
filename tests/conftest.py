import numpy as np
import pandas as pd
import pytest


def make_frame(
    n_days: int, seed: int, start: str = "2023-01-02", drift: float = 0.0005
) -> pd.DataFrame:
    """Synthetic daily bars shaped like PriceStore.load_daily output."""
    rng = np.random.default_rng(seed)
    dates = pd.DatetimeIndex(pd.bdate_range(start, periods=n_days), name="date")
    rets = rng.normal(drift, 0.01, n_days)
    close = 100 * np.cumprod(1 + rets)
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adj_close": close,
            "volume": rng.integers(1_000_000, 5_000_000, n_days).astype(float),
        },
        index=dates,
    )


@pytest.fixture
def synthetic_frames() -> dict[str, pd.DataFrame]:
    return {f"T{i}": make_frame(420, seed=i) for i in range(3)}
