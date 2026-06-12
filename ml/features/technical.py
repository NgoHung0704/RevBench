"""Causal technical features (docs/PLAN.md 2.4).

Every value at date t is computed from data through close(t) only — enforced by
tests/test_features.py::test_features_are_causal (truncating the future must not
change the past).
"""

import numpy as np
import pandas as pd

from data_pipeline.universe import HORIZON_DAYS

from ..data import make_labels

WARMUP_DAYS = 260  # longest lookback (252) + slack; rows before this are dropped


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, min_periods=window).mean()
    return 100 - 100 / (1 + gain / loss)


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    close, volume = df["adj_close"], df["volume"]
    ret_1 = close.pct_change()

    out = pd.DataFrame(index=df.index)
    out["ret_1"] = ret_1
    out["ret_5"] = close.pct_change(5)
    out["ret_21"] = close.pct_change(21)
    out["ret_63"] = close.pct_change(63)
    out["ret_252_21"] = close.shift(21) / close.shift(252) - 1  # classic 12-1 momentum
    out["vol_21"] = ret_1.rolling(21).std() * np.sqrt(252)
    out["vol_63"] = ret_1.rolling(63).std() * np.sqrt(252)
    out["rsi_14"] = rsi(close)

    ema12 = close.ewm(span=12, min_periods=12).mean()
    ema26 = close.ewm(span=26, min_periods=26).mean()
    macd = ema12 - ema26
    out["macd_hist"] = (macd - macd.ewm(span=9, min_periods=9).mean()) / close

    ma20 = close.rolling(20).mean()
    sd20 = close.rolling(20).std()
    out["bb_pctb"] = (close - (ma20 - 2 * sd20)) / (4 * sd20)

    out["volume_z"] = (volume - volume.rolling(21).mean()) / volume.rolling(21).std()
    out["px_ma50"] = close / close.rolling(50).mean() - 1
    out["px_ma200"] = close / close.rolling(200).mean() - 1
    out["dist_52w_high"] = close / close.rolling(252).max() - 1
    out["dow"] = out.index.dayofweek
    out["month"] = out.index.month
    return out


def build_dataset(
    frames: dict[str, pd.DataFrame], horizon: int = HORIZON_DAYS
) -> tuple[pd.DataFrame, pd.Series]:
    """-> (X, y) in long format, MultiIndex (date, ticker), warmup rows dropped.

    y is NaN on the last horizon+1 rows of each ticker (forward window unknown);
    the engine excludes those from training and scoring but still predicts them.
    """
    xs, ys = [], []
    for ticker, df in frames.items():
        feats = compute_features(df).iloc[WARMUP_DAYS:].dropna()
        label = make_labels(df["adj_close"], horizon).loc[feats.index]
        idx = pd.MultiIndex.from_arrays(
            [feats.index, [ticker] * len(feats)], names=["date", "ticker"]
        )
        xs.append(feats.set_axis(idx))
        ys.append(label.set_axis(idx))
    X = pd.concat(xs).sort_index()
    y = pd.concat(ys).sort_index()
    return X, y
