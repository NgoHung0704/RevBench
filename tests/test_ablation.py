import numpy as np
import pandas as pd

from ml.analysis.ablation import ic


def _panels(n_days: int, seed: int, noise: float):
    """A signal panel and a forward-return panel with a controllable relationship."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-01-01", periods=n_days)
    tickers = ["AAA", "BBB", "CCC"]
    sig = pd.DataFrame(rng.normal(size=(n_days, len(tickers))), index=idx, columns=tickers)
    ret = sig * 0.01 + rng.normal(scale=noise, size=sig.shape)
    return sig, ret


def test_ic_detects_a_positive_relationship():
    sig, ret = _panels(200, seed=0, noise=0.001)  # signal dominates the noise
    value, n = ic(sig, ret)
    assert n == 600
    assert value > 0.5


def test_ic_is_near_zero_for_unrelated_series():
    sig, _ = _panels(200, seed=1, noise=0.0)
    _, ret = _panels(200, seed=2, noise=0.0)  # independent draw
    value, n = ic(sig, ret)
    assert n == 600
    assert abs(value) < 0.2


def test_ic_reports_zero_samples_when_there_is_no_overlap():
    sig, ret = _panels(10, seed=3, noise=0.01)
    ret.index = ret.index + pd.Timedelta(days=365)  # disjoint dates
    value, n = ic(sig, ret)
    assert n == 0
    assert np.isnan(value)


def test_ic_ignores_tickers_absent_from_returns():
    sig, ret = _panels(50, seed=4, noise=0.01)
    value, n = ic(sig, ret[["AAA"]])
    assert n == 50  # only the shared ticker contributes
    assert not np.isnan(value)


def test_ic_on_empty_panel():
    value, n = ic(pd.DataFrame(), pd.DataFrame())
    assert n == 0
    assert np.isnan(value)
