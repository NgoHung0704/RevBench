"""Ablation: do the agents add anything on top of the ML baseline? (PLAN 8.2)

This is the project's central research question. The honest comparison at the
current sample size is at the **signal level** — the Information Coefficient of
each configuration against forward returns — *not* a walk-forward backtest:
agent history spans weeks, which is nowhere near enough independent periods to
train and test walk-forward without fooling ourselves.

Configurations compared (an ablation of the production fusion):

    ML-only      ml_proba - 0.5        the model's directional edge alone
    Agents-only  mean(agent signals)   news + technical + fundamentals agents
    ML + agents  fused score           exactly what the live system publishes

plus each individual agent, so a positive blend can be attributed.

Point-in-time: `agent_signals.as_of_date = t` is produced by the nightly run
after the US close on t, from data available at t, so it is aligned against the
return from close(t) to close(t+h) — the standard IC convention. The live system
additionally executes with a skip-a-day (decide at close t, fill at close t+1),
so realized performance would differ from the IC shown here.

⚠️ Read the sample size before the number. Overlapping h-day forward returns mean
the *effective* independent sample is roughly n / h — a few weeks of history is
INDICATIVE at best, never conclusive.

    python -m ml.analysis.ablation [--db PATH] [--horizon 5]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import HORIZON_DAYS

from ..data import load_frames

AGENTS = ("news", "technical", "fundamentals")


def _panel(df: pd.DataFrame, value: str) -> pd.DataFrame:
    """Long (date, ticker, value) -> wide date x ticker panel."""
    if df.empty:
        return pd.DataFrame()
    out = df.pivot_table(index="as_of_date", columns="ticker", values=value)
    out.index = pd.to_datetime(out.index)
    return out.sort_index()


def load_agent_signals(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(
            "SELECT ticker, as_of_date, agent, signal, confidence FROM agent_signals"
        ).fetchdf()
    finally:
        con.close()


def load_recommendations(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return con.execute(
            "SELECT ticker, as_of_date, score, ml_proba FROM recommendations"
        ).fetchdf()
    finally:
        con.close()


def forward_returns(db_path: str | Path, horizon: int) -> pd.DataFrame:
    frames = load_frames(db_path)
    return pd.DataFrame(
        {t: f["adj_close"].shift(-horizon) / f["adj_close"] - 1.0 for t, f in frames.items()}
    )


def ic(panel: pd.DataFrame, fwd: pd.DataFrame) -> tuple[float, int]:
    """Pooled Spearman IC of a signal panel vs forward returns, with sample size."""
    if panel.empty:
        return float("nan"), 0
    sig, ret = [], []
    for ticker in [c for c in panel.columns if c in fwd.columns]:
        joined = pd.concat(
            [panel[ticker].rename("s"), fwd[ticker].rename("r")], axis=1, sort=True
        ).dropna()
        if not joined.empty:
            sig.append(joined["s"])
            ret.append(joined["r"])
    if not sig:
        return float("nan"), 0
    s, r = pd.concat(sig), pd.concat(ret)
    n = len(s)
    return (float(s.corr(r, method="spearman")) if n > 2 else float("nan")), n


def run_ablation(
    db_path: str | Path = DEFAULT_DB_PATH, horizon: int = HORIZON_DAYS
) -> dict:
    signals = load_agent_signals(db_path)
    recs = load_recommendations(db_path)
    fwd = forward_returns(db_path, horizon)

    per_agent = {a: _panel(signals[signals["agent"] == a], "signal") for a in AGENTS}
    available = {a: p for a, p in per_agent.items() if not p.empty}

    # Agents-only: equal-weight mean of whichever agents produced a signal.
    agents_only = (
        pd.concat(available.values()).groupby(level=0).mean() if available else pd.DataFrame()
    )
    ml_only = _panel(recs, "ml_proba")
    if not ml_only.empty:
        ml_only = ml_only - 0.5  # centre the probability so its sign is a direction
    fused = _panel(recs, "score")

    configs = {
        "ML-only (ml_proba - 0.5)": ml_only,
        "Agents-only (mean signal)": agents_only,
        "ML + agents (fused score)": fused,
    }
    configs.update({f"  agent: {a}": p for a, p in per_agent.items()})

    rows = []
    for name, panel in configs.items():
        value, n = ic(panel, fwd)
        rows.append({"config": name, "ic": value, "n": n})

    date_range = None
    if not signals.empty:
        dates = pd.to_datetime(signals["as_of_date"]).sort_values()
        date_range = (str(dates.iloc[0].date()), str(dates.iloc[-1].date()))

    return {
        "rows": rows,
        "horizon": horizon,
        "agent_dates": int(signals["as_of_date"].nunique()) if not signals.empty else 0,
        "agent_rows": int(len(signals)),
        "rec_dates": int(recs["as_of_date"].nunique()) if not recs.empty else 0,
        "date_range": date_range,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent-alpha ablation (IC based).")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="DuckDB path")
    parser.add_argument("--horizon", type=int, default=HORIZON_DAYS, help="forward-return days")
    args = parser.parse_args(argv)

    res = run_ablation(args.db, args.horizon)

    print("Agent-alpha ablation - Information Coefficient (Spearman) vs forward returns")
    print(f"  horizon        : {res['horizon']} trading days")
    print(f"  agent signals  : {res['agent_rows']} rows over {res['agent_dates']} distinct dates")
    print(f"  recommendations: {res['rec_dates']} distinct dates")
    print(f"  date range     : {res['date_range']}")
    print()
    print(f"  {'configuration':<28} {'IC':>9} {'n':>7}")
    print(f"  {'-' * 28} {'-' * 9} {'-' * 7}")
    for row in res["rows"]:
        value = "     n/a" if pd.isna(row["ic"]) else f"{row['ic']:+.4f}"
        print(f"  {row['config']:<28} {value:>9} {row['n']:>7}")

    eff = max((r["n"] for r in res["rows"]), default=0) // max(res["horizon"], 1)
    print()
    print("  [!] Sample size first. Forward returns overlap, so the effective independent")
    print(f"      sample is roughly n/horizon (~{eff} periods here). With only a few weeks")
    print("      of agent history this is INDICATIVE, not conclusive (docs/REVISIT.md R1).")
    if res["agent_dates"] < 60:
        print("      Fewer than ~60 dates: treat any ranking between configurations as noise")
        print("      and let the nightly scheduler keep accumulating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
