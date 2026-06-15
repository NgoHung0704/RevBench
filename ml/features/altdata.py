"""Alt-data attention feature + Information Coefficient (docs/PLAN.md 5.4).

Google Trends gives years of history, so unlike the news-sentiment feature this
one actually overlaps the price-backtest window and its IC is measurable.

Feature: ASVI (abnormal search volume index, after Da/Engelberg/Gao 2011) —
the current search interest relative to its trailing median. Point-in-time: each
weekly value is keyed by its `available_at` (week-end + reporting lag), and for a
trading day t we use the most recent value available by t (merge_asof backward).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH, AltDataStore
from data_pipeline.universe import HORIZON_DAYS

from ..data import load_frames


def attention_feature(altdata: pd.DataFrame, window: int = 8) -> pd.DataFrame:
    """ASVI panel indexed by `available_at` (the day each value became usable)."""
    if altdata.empty:
        return pd.DataFrame()
    df = altdata.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["available_at"] = pd.to_datetime(df["available_at"]).dt.normalize()

    series: dict[str, pd.Series] = {}
    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date")
        median = g["value"].rolling(window, min_periods=max(2, window // 2)).median()
        asvi = g["value"] / median - 1.0
        s = pd.Series(asvi.to_numpy(), index=pd.DatetimeIndex(g["available_at"]))
        series[ticker] = s[~s.index.duplicated(keep="last")]
    return pd.DataFrame(series).sort_index()


def _forward_returns(frames: dict[str, pd.DataFrame], horizon: int) -> pd.DataFrame:
    return pd.DataFrame(
        {t: f["adj_close"].shift(-horizon) / f["adj_close"] - 1.0 for t, f in frames.items()}
    )


def _point_in_time_align(feature: pd.Series, forward: pd.Series) -> pd.DataFrame:
    """For each trading day, take the latest feature available by that day."""
    f = feature.dropna()
    trading = forward.dropna()
    if f.empty or trading.empty:
        return pd.DataFrame(columns=["f", "r"])
    merged = pd.merge_asof(
        pd.DataFrame({"day": trading.index}).sort_values("day"),
        pd.DataFrame({"av": f.index, "f": f.to_numpy()}).sort_values("av"),
        left_on="day", right_on="av", direction="backward",
    )
    aligned = pd.Series(merged["f"].to_numpy(), index=merged["day"])
    return pd.concat([aligned.rename("f"), trading.rename("r")], axis=1).dropna()


def altdata_ic(
    db_path: str | Path = DEFAULT_DB_PATH,
    source: str = "google_trends",
    horizon: int = HORIZON_DAYS,
    window: int = 8,
) -> dict:
    with AltDataStore(db_path) as store:
        altdata = store.load(source)
    panel = attention_feature(altdata, window)
    if panel.empty:
        return {"ic": float("nan"), "n": 0, "note": f"no {source} data"}

    fwd = _forward_returns(load_frames(db_path), horizon)
    fs, rs = [], []
    for ticker in (t for t in panel.columns if t in fwd.columns):
        joined = _point_in_time_align(panel[ticker], fwd[ticker])
        fs.append(joined["f"])
        rs.append(joined["r"])
    f = pd.concat(fs) if fs else pd.Series(dtype=float)
    r = pd.concat(rs) if rs else pd.Series(dtype=float)
    n = len(f)
    ic = float(f.corr(r, method="spearman")) if n > 2 else float("nan")
    return {"ic": ic, "n": n, "source": source, "horizon": horizon, "window": window}


def main(argv: list[str] | None = None) -> int:
    """python -m ml.features.altdata [--source wikipedia] -- print the attention IC."""
    import argparse

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--source", default="wikipedia")
    parser.add_argument("--window", type=int, default=30, help="trailing median window (days)")
    args = parser.parse_args(argv)

    result = altdata_ic(source=args.source, window=args.window)
    print(f"Alt-data Information Coefficient (Spearman) -- source: {result.get('source')}")
    print(f"  IC          : {result['ic']:.4f}")
    print(f"  sample size : {result['n']}")
    if result["n"] > 2:
        print(f"  horizon {result['horizon']}d, window {result['window']}")
        print("\n  This source has years of history, so (unlike news) the IC is measurable.")
        print("  IC ~0.02-0.05 is a typical weak-but-real signal; a single in-sample read --")
        print("  confirm incremental value in the walk-forward backtest before trusting it.")
    else:
        print("\n  No overlap yet -- run: python -m data_pipeline.altdata.fetch --all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
