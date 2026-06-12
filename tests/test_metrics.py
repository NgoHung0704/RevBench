import numpy as np
import pandas as pd

from ml.backtest.metrics import (
    annualized_return,
    max_drawdown,
    sharpe,
    sortino,
    summarize,
)


def series(values) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2025-01-02", periods=len(values)))


def test_max_drawdown_known_value():
    assert np.isclose(max_drawdown(series([0.10, -0.50])), -0.50)


def test_sharpe_zero_mean():
    assert abs(sharpe(series([0.01, -0.01] * 100))) < 1e-9


def test_sharpe_nan_on_zero_vol():
    assert np.isnan(sharpe(series([0.001] * 50)))


def test_sortino_nan_without_losing_days():
    assert np.isnan(sortino(series([0.001, 0.002] * 25)))


def test_annualized_return_one_year():
    daily = series([0.001] * 252)
    assert np.isclose(annualized_return(daily), 1.001**252 - 1)


def test_summarize_keys():
    out = summarize(series([0.01, -0.005, 0.002] * 30))
    assert set(out) == {
        "total_return", "ann_return", "ann_vol", "sharpe", "sortino", "max_drawdown",
    }
