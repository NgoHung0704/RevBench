"""Walk-forward backtest CLI (docs/PLAN.md Phase 2 Done criterion).

Usage:
    python -m ml.backtest --model all
    python -m ml.backtest --model lgbm --tickers AAPL MSFT NVDA

Prints out-of-sample metrics for the requested model(s) next to the baselines
and equal-weight buy & hold over the identical evaluation window.
"""

import argparse

import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import TICKERS

from ..data import load_frames, returns_panel
from ..features.technical import build_dataset
from ..models.baselines import AlwaysUp, MomentumSign
from ..models.lgbm import LGBMSignal
from .engine import BacktestConfig, run_backtest
from .metrics import summarize

MODEL_FACTORIES = {
    "lgbm": lambda cfg: LGBMSignal(seed=cfg.seed),
    "momentum": lambda cfg: MomentumSign(),
    "always_up": lambda cfg: AlwaysUp(),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="all", choices=[*MODEL_FACTORIES, "all"], help="model to backtest"
    )
    parser.add_argument("--tickers", nargs="+", metavar="T", help="subset (default: universe)")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="DuckDB path")
    args = parser.parse_args(argv)

    tickers = tuple(t.upper() for t in args.tickers) if args.tickers else TICKERS
    names = list(MODEL_FACTORIES) if args.model == "all" else [args.model]
    config = BacktestConfig()

    frames = load_frames(args.db, tickers)
    if not frames:
        print("No price data found — run: python -m data_pipeline.fetch --all --years 5")
        return 1
    X, y = build_dataset(frames)
    rets = returns_panel(frames)

    rows: dict[str, dict] = {}
    benchmark = None
    for name in names:
        result = run_backtest(lambda name=name: MODEL_FACTORIES[name](config), X, y, rets, config)
        rows[name] = {
            "accuracy": result.accuracy,
            "exposure": result.exposure,
            "turnover_yr": result.annual_turnover,
            **summarize(result.net_returns),
        }
        benchmark = result.benchmark  # identical window for every model
        base_rate = result.base_rate
    rows["buy_and_hold"] = {
        "accuracy": float("nan"),
        "exposure": 1.0,
        "turnover_yr": 0.0,
        **summarize(benchmark),
    }

    table = pd.DataFrame(rows).T
    n_days = len(benchmark)
    print(
        f"Walk-forward OOS: {n_days} trading days "
        f"({benchmark.index.min().date()} -> {benchmark.index.max().date()}), "
        f"{len(frames)} tickers, horizon {config.horizon}d, "
        f"cost {config.cost_bps:.0f} bps/side, embargo {config.embargo_days}d"
    )
    print(f"Label base rate (share of up-moves): {base_rate:.1%}\n")
    with pd.option_context("display.float_format", "{:,.3f}".format, "display.width", 140):
        print(table.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
