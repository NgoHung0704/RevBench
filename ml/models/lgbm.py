"""LightGBM direction classifier (docs/PLAN.md 2.5).

Gradient boosting on tabular features is the sane default for low-frequency
financial ML at this data size (~15k rows); deep nets come later only if this
clears the baselines. Modest capacity + heavy subsampling because the signal,
if any, is tiny.
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from .base import SignalModel


class LGBMSignal(SignalModel):
    name = "lgbm"

    def __init__(self, seed: int = 42):
        self.model = LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=50,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            random_state=seed,
            force_row_wise=True,  # deterministic histogram construction
            verbosity=-1,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.model.fit(X, y.astype(int))

    def predict_proba_up(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]
