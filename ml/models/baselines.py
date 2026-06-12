"""Baselines (docs/PLAN.md 2.3) — the floor every real model must beat.

AlwaysUp ~ buy-and-hold pushed through the exact same cost/timing machinery
(internal consistency check). MomentumSign is the classic 12-1 momentum effect —
the strongest free lunch in the academic literature, and a much tougher baseline
than ARIMA on near-white-noise daily returns.
"""

import numpy as np
import pandas as pd

from .base import SignalModel


class AlwaysUp(SignalModel):
    name = "always_up"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        pass

    def predict_proba_up(self, X: pd.DataFrame) -> np.ndarray:
        return np.ones(len(X))


class MomentumSign(SignalModel):
    name = "momentum"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        pass

    def predict_proba_up(self, X: pd.DataFrame) -> np.ndarray:
        return np.where(X["ret_252_21"] > 0, 0.6, 0.4)
