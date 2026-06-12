"""CLI: fetch quarterly fundamentals from SEC EDGAR into DuckDB.

Usage:
    python -m data_pipeline.fundamentals.fetch --tickers AAPL
    python -m data_pipeline.fundamentals.fetch --all
"""

import argparse

from ..store import DEFAULT_DB_PATH, FundamentalsStore
from ..universe import TICKERS
from .edgar import EdgarClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tickers", nargs="+", metavar="T", help="tickers to fetch")
    group.add_argument("--all", action="store_true", help="fetch the whole universe")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="DuckDB path")
    args = parser.parse_args(argv)

    tickers = list(TICKERS) if args.all else [t.upper() for t in args.tickers]
    client = EdgarClient()
    failed: list[str] = []
    with FundamentalsStore(args.db) as store:
        for ticker in tickers:
            try:
                df = client.quarterly_facts(ticker)
            except Exception as exc:
                print(f"{ticker}: FAILED — {exc}")
                failed.append(ticker)
                continue
            n = store.upsert(df)
            span = (
                f"{df['period_end'].min().date()} -> {df['period_end'].max().date()}"
                if n else "no rows"
            )
            print(f"{ticker}: {n} fact rows ({span})")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
