"""Walk-forward backtest engine (docs/PLAN.md 2.1, docs/DECISIONS.md D11).

Scheme: expanding train window -> embargo gap -> fixed test window, repeated.
The embargo (horizon + 1 trading days) purges label overlap: the last training
label must settle strictly before the first test date, or the model trains on
prices it will be tested against (Lopez de Prado's purged CV).

Execution model (see ml/data.py): decision from features at t, fill at
close(t+1), so a position first earns the return of day t+2 — positions are the
raw signal shifted by 2 trading days. Costs are charged on position changes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from data_pipeline.universe import HORIZON_DAYS

from ..models.base import SignalModel


@dataclass(frozen=True)
class BacktestConfig:
    horizon: int = HORIZON_DAYS
    min_train_days: int = 504  # ~2 years before the first prediction
    test_window_days: int = 63  # ~1 quarter per fold
    embargo_days: int = HORIZON_DAYS + 1
    cost_bps: float = 10.0  # per side: commission-free broker, spread + slippage
    prob_threshold: float = 0.5
    seed: int = 42


@dataclass(frozen=True)
class Fold:
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


@dataclass
class BacktestResult:
    model_name: str
    proba: pd.Series  # OOS only, MultiIndex (date, ticker)
    folds: list[Fold]
    accuracy: float
    base_rate: float
    gross_returns: pd.Series = field(default=None)  # type: ignore[assignment]
    net_returns: pd.Series = field(default=None)  # type: ignore[assignment]
    benchmark: pd.Series = field(default=None)  # type: ignore[assignment]
    annual_turnover: float = float("nan")
    exposure: float = float("nan")


def walk_forward(
    model_factory: Callable[[], SignalModel],
    X: pd.DataFrame,
    y: pd.Series,
    config: BacktestConfig,
) -> tuple[pd.Series, list[Fold]]:
    """Out-of-sample probabilities for every date past the initial train window."""
    dates = X.index.get_level_values("date").unique().sort_values()
    date_level = X.index.get_level_values("date")
    oos: list[pd.Series] = []
    folds: list[Fold] = []

    start = config.min_train_days
    while start < len(dates):
        test_dates = dates[start : start + config.test_window_days]
        train_cutoff = dates[start - config.embargo_days]  # train strictly before
        train_mask = (date_level < train_cutoff) & y.notna().values
        test_mask = date_level.isin(test_dates)

        model = model_factory()
        model.fit(X[train_mask], y[train_mask])
        proba = model.predict_proba_up(X[test_mask])

        oos.append(pd.Series(proba, index=X.index[test_mask]))
        folds.append(
            Fold(
                train_end=dates[start - config.embargo_days - 1],
                test_start=test_dates[0],
                test_end=test_dates[-1],
            )
        )
        start += config.test_window_days

    return pd.concat(oos).sort_index(), folds


def run_backtest(
    model_factory: Callable[[], SignalModel],
    X: pd.DataFrame,
    y: pd.Series,
    rets: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    config = config or BacktestConfig()
    proba, folds = walk_forward(model_factory, X, y, config)

    scored = y.loc[proba.index]
    valid = scored.notna()
    predictions = proba[valid] > 0.5
    accuracy = float((predictions == scored[valid].astype(bool)).mean())
    base_rate = float(scored[valid].mean())

    result = BacktestResult(
        model_name=model_factory().name,
        proba=proba,
        folds=folds,
        accuracy=accuracy,
        base_rate=base_rate,
    )
    _attach_strategy(result, rets, config)
    return result


def _attach_strategy(result: BacktestResult, rets: pd.DataFrame, config: BacktestConfig) -> None:
    """Signal -> positions -> net daily returns, fixed 1/N weights (no leverage)."""
    n_universe = rets.shape[1]
    proba_wide = result.proba.unstack("ticker").reindex(columns=rets.columns)
    raw_pos = (proba_wide > config.prob_threshold).astype(float).fillna(0.0)

    # decision at t -> fill at close(t+1) -> first return earned on day t+2
    pos = raw_pos.shift(2).fillna(0.0)
    window = pos.index
    day_rets = rets.loc[window].fillna(0.0)

    turnover = pos.diff().abs()
    turnover.iloc[0] = pos.iloc[0]  # entering the very first positions from cash

    gross = (pos * day_rets).sum(axis=1) / n_universe
    costs = turnover.sum(axis=1) / n_universe * (config.cost_bps / 1e4)

    result.gross_returns = gross
    result.net_returns = gross - costs
    result.benchmark = day_rets.mean(axis=1)  # equal-weight buy & hold, same window
    result.annual_turnover = float(turnover.sum(axis=1).mean() / n_universe * 252)
    result.exposure = float(pos.sum(axis=1).mean() / n_universe)
