"""Signal model interface (docs/PLAN.md 2.5).

A model maps a feature row at date t to P(price up over the next H days,
executed at close t+1). Baselines and ML models share this interface so the
backtest engine treats them identically — apples-to-apples comparison.
"""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class SignalModel(ABC):
    name: str

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...

    @abstractmethod
    def predict_proba_up(self, X: pd.DataFrame) -> np.ndarray:
        """P(label == 1) per row of X, in [0, 1]."""
