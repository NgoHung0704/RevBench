import numpy as np
import pandas as pd
import pytest

from ml.backtest.engine import BacktestConfig, run_backtest, walk_forward
from ml.data import returns_panel
from ml.features.technical import build_dataset
from ml.models.base import SignalModel
from ml.models.baselines import AlwaysUp, MomentumSign
from ml.models.lgbm import LGBMSignal

CFG = BacktestConfig(min_train_days=60, test_window_days=21, embargo_days=6)


@pytest.fixture
def dataset(synthetic_frames):
    X, y = build_dataset(synthetic_frames, horizon=5)
    rets = returns_panel(synthetic_frames)
    return X, y, rets


class Cheat(SignalModel):
    """Reads the label it is asked to predict — only valid as an alignment probe."""

    name = "cheat"

    def __init__(self, y: pd.Series):
        self._y = y

    def fit(self, X, y):
        pass

    def predict_proba_up(self, X):
        return self._y.loc[X.index].fillna(0.5).to_numpy()


def test_cheat_model_scores_perfectly(dataset):
    """If labels and predictions are aligned through the whole engine, a model
    that peeks at the answer must score 100% — anything less means misalignment."""
    X, y, rets = dataset
    result = run_backtest(lambda: Cheat(y), X, y, rets, CFG)
    assert result.accuracy == 1.0


def test_embargo_gap_respected(dataset):
    X, y, rets = dataset
    _, folds = walk_forward(lambda: AlwaysUp(), X, y, CFG)
    dates = X.index.get_level_values("date").unique().sort_values()
    assert len(folds) >= 3
    for fold in folds:
        gap = dates.get_loc(fold.test_start) - dates.get_loc(fold.train_end)
        # last train label settles at train_end + 1 + horizon < test_start
        assert gap > CFG.horizon + 1


def test_deterministic_given_same_inputs(dataset):
    X, y, rets = dataset
    a = run_backtest(lambda: MomentumSign(), X, y, rets, CFG)
    b = run_backtest(lambda: MomentumSign(), X, y, rets, CFG)
    pd.testing.assert_series_equal(a.net_returns, b.net_returns)


def test_always_up_tracks_buy_and_hold(dataset):
    """AlwaysUp through the cost machinery = buy & hold minus one entry cost."""
    X, y, rets = dataset
    result = run_backtest(lambda: AlwaysUp(), X, y, rets, CFG)
    # exposure ramps to 1 after the 2-day execution lag
    assert result.exposure > 0.95
    diff = (result.gross_returns.iloc[2:] - result.benchmark.iloc[2:]).abs().max()
    assert diff < 1e-12


def test_costs_reduce_returns(dataset):
    X, y, rets = dataset
    result = run_backtest(lambda: MomentumSign(), X, y, rets, CFG)
    assert (result.net_returns <= result.gross_returns + 1e-15).all()


def test_lgbm_smoke(dataset):
    X, y, rets = dataset
    result = run_backtest(lambda: LGBMSignal(seed=42), X, y, rets, CFG)
    p = result.proba.to_numpy()
    assert np.isfinite(p).all() and (p >= 0).all() and (p <= 1).all()
    assert 0.2 < result.accuracy < 0.8  # noise data — anything extreme is a bug
