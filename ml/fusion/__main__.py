"""Fusion CLI (docs/PLAN.md 4.2): generate + store today's recommendations.

Usage:
    python -m ml.fusion                       # whole universe
    python -m ml.fusion --tickers AAPL MSFT

Reads precomputed agent signals + trains the ML model on price history, fuses
them into one Buy/Hold/Sell per ticker. No LLM calls here.
"""

import argparse

from agents.store import AgentStore
from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import TICKERS

from .fuse import generate_recommendations
from .store import RecommendationStore

ARROW = {"buy": "BUY ", "hold": "HOLD", "sell": "SELL"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", metavar="T")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--no-store", action="store_true", help="print only, don't persist")
    args = parser.parse_args(argv)

    tickers = tuple(t.upper() for t in args.tickers) if args.tickers else TICKERS

    with AgentStore(args.db) as agent_store:
        recs = generate_recommendations(args.db, agent_store, tickers)
    if not recs:
        print("No data — fetch prices and run agents first.")
        return 1

    if not args.no_store:
        with RecommendationStore(args.db) as store:
            store.upsert(recs)

    print(f"as_of {recs[0].as_of_date} -- {len(recs)} recommendations "
          f"{'(not stored)' if args.no_store else ''}\n")
    for r in sorted(recs, key=lambda x: x.score, reverse=True):
        comps = " ".join(f"{k}={v:+.2f}" for k, v in r.components.items())
        print(f"  {ARROW[r.action]} {r.ticker:>5}  score={r.score:+.2f}"
              f" conf={r.confidence:.2f}  [{comps}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
