"""Price data-quality checks (docs/PLAN.md 1.6).

Run: python -m data_pipeline.quality
"""

from datetime import date

import numpy as np
import pandas as pd

from .store import DEFAULT_DB_PATH, PriceStore

EXTREME_DAILY_MOVE = 0.30  # |return| above this suggests an unadjusted split
GAP_BDAYS = 3  # single missing business days are holidays; runs this long are data gaps
STALE_DAYS = 7


def check_price_frame(df: pd.DataFrame, ticker: str, as_of: date | None = None) -> list[str]:
    """Return a list of human-readable issues; empty list means clean."""
    if df.empty:
        return [f"{ticker}: no data"]
    issues: list[str] = []
    idx = pd.DatetimeIndex(pd.to_datetime(df.index)).sort_values()

    expected = pd.bdate_range(idx.min(), idx.max())
    missing = expected.difference(idx)
    if len(missing):
        pos = expected.get_indexer(missing)
        runs = np.split(np.arange(len(pos)), np.where(np.diff(pos) != 1)[0] + 1)
        for run in runs:
            if len(run) >= GAP_BDAYS:
                issues.append(
                    f"{ticker}: {len(run)} consecutive business days missing"
                    f" from {missing[run[0]].date()}"
                )

    returns = pd.Series(df["adj_close"].values, index=idx).pct_change().abs().dropna()
    for day, move in returns[returns > EXTREME_DAILY_MOVE].items():
        issues.append(f"{ticker}: {move:.0%} daily move on {day.date()} (unadjusted split?)")

    zero_volume = int((df["volume"] == 0).sum())
    if zero_volume:
        issues.append(f"{ticker}: {zero_volume} zero-volume days")

    if as_of is not None and (as_of - idx.max().date()).days > STALE_DAYS:
        issues.append(f"{ticker}: stale — last bar {idx.max().date()}")

    return issues


def run_report(db_path=DEFAULT_DB_PATH, as_of: date | None = None) -> list[str]:
    issues: list[str] = []
    with PriceStore(db_path) as store:
        for ticker in store.coverage()["ticker"].unique():
            issues += check_price_frame(store.load_daily(ticker), ticker, as_of)
    return issues


def main() -> int:
    issues = run_report(as_of=date.today())
    if not issues:
        print("All clean.")
        return 0
    for issue in issues:
        print(issue)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
