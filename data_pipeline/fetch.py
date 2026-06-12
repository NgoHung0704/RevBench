"""CLI: fetch daily prices into the local DuckDB store.

Usage:
    python -m data_pipeline.fetch --tickers AAPL --years 1
    python -m data_pipeline.fetch --all --years 5
"""

import argparse
from datetime import date, timedelta

from .providers.yfinance_provider import YFinanceProvider
from .store import DEFAULT_DB_PATH, PriceStore
from .universe import TICKERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tickers", nargs="+", metavar="T", help="tickers to fetch")
    group.add_argument("--all", action="store_true", help="fetch the whole universe")
    parser.add_argument("--years", type=float, default=5, help="history length (default 5)")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="DuckDB path")
    args = parser.parse_args(argv)

    tickers = list(TICKERS) if args.all else [t.upper() for t in args.tickers]
    end = date.today()
    start = end - timedelta(days=round(args.years * 365.25))

    provider = YFinanceProvider()
    failed: list[str] = []
    with PriceStore(args.db) as store:
        for ticker in tickers:
            try:
                df = provider.fetch_daily(ticker, start, end)
            except Exception as exc:  # one bad ticker must not kill the batch
                print(f"{ticker}: FAILED — {exc}")
                failed.append(ticker)
                continue
            n = store.upsert_daily(ticker, df, provider.name)
            # ASCII only: Windows consoles often run cp1252
            print(
                f"{ticker}: {n} rows "
                f"({df.index.min().date()} -> {df.index.max().date()})"
            )
        print("\nCoverage:")
        print(store.coverage().to_string(index=False))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
