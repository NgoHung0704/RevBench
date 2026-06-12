"""Strategy metrics (docs/PLAN.md 2.2) — the shared yardstick, forever.

All inputs are daily simple-return series. Annualization uses 252 trading days.
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def annualized_return(daily: pd.Series) -> float:
    """CAGR implied by the compounded path."""
    if daily.empty:
        return float("nan")
    total = float((1 + daily).prod())
    years = len(daily) / TRADING_DAYS
    if total <= 0 or years == 0:
        return float("nan")
    return total ** (1 / years) - 1


def annualized_vol(daily: pd.Series) -> float:
    return float(daily.std() * np.sqrt(TRADING_DAYS))


def sharpe(daily: pd.Series) -> float:
    vol = daily.std()
    if vol == 0 or np.isnan(vol):
        return float("nan")
    return float(daily.mean() / vol * np.sqrt(TRADING_DAYS))


def sortino(daily: pd.Series) -> float:
    downside = daily[daily < 0]
    if len(downside) == 0:
        return float("nan")  # no losing days observed — not enough information
    dd = downside.std()
    if dd == 0 or np.isnan(dd):
        return float("nan")
    return float(daily.mean() / dd * np.sqrt(TRADING_DAYS))


def max_drawdown(daily: pd.Series) -> float:
    """Most negative peak-to-trough of the compounded equity curve."""
    equity = (1 + daily).cumprod()
    return float((equity / equity.cummax() - 1).min())


def summarize(daily: pd.Series) -> dict[str, float]:
    return {
        "total_return": float((1 + daily).prod() - 1),
        "ann_return": annualized_return(daily),
        "ann_vol": annualized_vol(daily),
        "sharpe": sharpe(daily),
        "sortino": sortino(daily),
        "max_drawdown": max_drawdown(daily),
    }
