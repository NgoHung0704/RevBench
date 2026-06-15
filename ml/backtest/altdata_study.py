"""Does Wikipedia attention add alpha over the technical baseline? (PLAN 4.5)

Runs the same walk-forward LightGBM twice — technical features only, then with
the attention feature added — on identical folds, and prints the metrics side by
side against buy & hold. This is the central research question, finally answerable
because the attention feature (unlike news sentiment) has years of history.

    python -m ml.backtest.altdata_study
"""

from data_pipeline.store import DEFAULT_DB_PATH, AltDataStore
from data_pipeline.universe import TICKERS

from ..data import load_frames, returns_panel
from ..features.altdata import attention_on_index
from ..features.technical import build_dataset
from ..models.lgbm import LGBMSignal
from .engine import BacktestConfig, run_backtest
from .metrics import summarize


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args(argv)

    frames = load_frames(args.db, TICKERS)
    if not frames:
        print("No price data — run data_pipeline.fetch first.")
        return 1
    X, y = build_dataset(frames)
    rets = returns_panel(frames)

    with AltDataStore(args.db) as store:
        altdata = store.load("wikipedia")
    attention = attention_on_index(altdata, X.index, window=args.window)
    X_alt = X.assign(wiki_attention=attention)

    config = BacktestConfig()
    base = run_backtest(lambda: LGBMSignal(seed=config.seed), X, y, rets, config)
    aug = run_backtest(lambda: LGBMSignal(seed=config.seed), X_alt, y, rets, config)

    # coverage of the attention feature over the out-of-sample rows actually scored
    oos = X.loc[base.proba.index]
    coverage = attention.loc[oos.index].notna().mean()

    print(f"Walk-forward OOS: {len(base.net_returns)} days, {len(frames)} tickers, "
          f"horizon {config.horizon}d, cost {config.cost_bps:.0f} bps/side")
    print(f"Attention feature coverage over scored rows: {coverage:.1%}\n")

    rows = {
        "lgbm (technical)": {"accuracy": base.accuracy, **summarize(base.net_returns)},
        "lgbm + wiki": {"accuracy": aug.accuracy, **summarize(aug.net_returns)},
        "buy_and_hold": {"accuracy": float("nan"), **summarize(base.benchmark)},
    }
    import pandas as pd

    table = pd.DataFrame(rows).T[
        ["accuracy", "sharpe", "ann_return", "max_drawdown", "total_return"]
    ]
    with pd.option_context("display.float_format", "{:,.3f}".format):
        print(table.to_string())

    d_acc = aug.accuracy - base.accuracy
    d_sharpe = summarize(aug.net_returns)["sharpe"] - summarize(base.net_returns)["sharpe"]
    print(f"\nDelta from adding attention:  accuracy {d_acc:+.4f}  Sharpe {d_sharpe:+.3f}")
    print("Honest read: a tiny delta on one in-sample window is noise, not proof. "
          "The attention IC is real (+0.025) but thin; treat any improvement as "
          "indicative until it holds across more history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
