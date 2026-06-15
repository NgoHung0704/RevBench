"""CLI: fetch alternative-data series into DuckDB.

Usage:
    python -m data_pipeline.altdata.fetch --source trends --tickers AAPL TSLA
    python -m data_pipeline.altdata.fetch --source trends --all --years 5
"""

import argparse
from datetime import date, timedelta

from ..store import DEFAULT_DB_PATH, AltDataStore
from ..universe import TICKERS
from .base import ProviderRateLimited
from .trends import GoogleTrendsProvider
from .wikipedia import WikipediaProvider

# Wikipedia is the working default; the unofficial Trends endpoint 429s (R14).
PROVIDERS = {"wikipedia": WikipediaProvider, "trends": GoogleTrendsProvider}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="wikipedia", choices=list(PROVIDERS))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tickers", nargs="+", metavar="T")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--years", type=float, default=5)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args(argv)

    tickers = list(TICKERS) if args.all else [t.upper() for t in args.tickers]
    end = date.today()
    start = end - timedelta(days=round(args.years * 365.25))

    provider = PROVIDERS[args.source]()
    failed: list[str] = []
    with AltDataStore(args.db) as store:
        for ticker in tickers:
            try:
                points = provider.fetch_series(ticker, start, end)
            except ProviderRateLimited as exc:
                print(f"{ticker}: rate-limited ({exc}) -- stopping, retry later")
                failed.append(ticker)
                break
            except Exception as exc:
                print(f"{ticker}: FAILED -- {exc}")
                failed.append(ticker)
                continue
            n = store.upsert(points)
            span = f"{points[0].date} -> {points[-1].date}" if points else "no data"
            print(f"{ticker}: {n} points ({span})")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
