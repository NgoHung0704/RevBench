import numpy as np
import pandas as pd
from conftest import make_frame

from ml.data import make_labels
from ml.features.technical import WARMUP_DAYS, build_dataset, compute_features, rsi


def test_features_are_causal():
    """Truncating the future must not change the past — the anti-lookahead gold test."""
    df = make_frame(400, seed=7)
    full = compute_features(df)
    truncated = compute_features(df.iloc[:300])
    pd.testing.assert_frame_equal(full.iloc[:300], truncated)


def test_no_nan_after_warmup():
    df = make_frame(400, seed=1)
    feats = compute_features(df).iloc[WARMUP_DAYS:]
    assert not feats.isna().any().any()


def test_rsi_high_on_strict_uptrend():
    close = pd.Series(
        np.linspace(100, 200, 120), index=pd.bdate_range("2025-01-02", periods=120)
    )
    assert rsi(close).iloc[-1] > 95


def test_make_labels_hand_checked():
    prices = pd.Series(
        [100, 102, 101, 105, 107, 103, 99, 104, 106, 108],
        index=pd.bdate_range("2026-01-05", periods=10),
        dtype=float,
    )
    y = make_labels(prices, horizon=2)  # settle(t+3) vs exec(t+1)
    assert y.iloc[0] == 1.0  # 105 > 102
    assert y.iloc[2] == 0.0  # 103 < 105
    assert y.iloc[6] == 1.0  # 108 > 104
    assert y.iloc[-3:].isna().all()  # forward window runs off the end


def test_build_dataset_shape(synthetic_frames):
    X, y = build_dataset(synthetic_frames, horizon=5)
    assert list(X.index.names) == ["date", "ticker"]
    assert len(X) == len(y)
    assert not X.isna().any().any()
    # exactly the last horizon+1 rows of each ticker have unknown labels
    assert int(y.isna().sum()) == (5 + 1) * len(synthetic_frames)
