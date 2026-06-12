"""Daily update jobs (docs/PLAN.md 1.5).

Run once now:   python -m data_pipeline.jobs
On a schedule:  python -m data_pipeline.scheduler
"""

import logging
from datetime import date, timedelta

from .fundamentals.edgar import EdgarClient
from .news.base import ProviderRateLimited
from .news.gdelt import GDELTProvider
from .news.rss import YahooRSSProvider
from .providers.yfinance_provider import YFinanceProvider
from .quality import run_report
from .store import DEFAULT_DB_PATH, FundamentalsStore, NewsStore, PriceStore
from .universe import TICKERS

logger = logging.getLogger("revbench.jobs")

PRICE_LOOKBACK_DAYS = 7  # re-fetch a week to heal gaps and late corrections


def update_prices(db_path=DEFAULT_DB_PATH) -> int:
    provider = YFinanceProvider()
    end = date.today()
    start = end - timedelta(days=PRICE_LOOKBACK_DAYS)
    total = 0
    with PriceStore(db_path) as store:
        for ticker in TICKERS:
            try:
                df = provider.fetch_daily(ticker, start, end)
            except Exception:  # one bad ticker must not kill the batch
                logger.exception("price fetch failed for %s", ticker)
                continue
            total += store.upsert_daily(ticker, df, provider.name)
    return total


def update_news(db_path=DEFAULT_DB_PATH) -> int:
    providers = [YahooRSSProvider(), GDELTProvider()]
    total = 0
    with NewsStore(db_path) as store:
        for provider in providers:
            for ticker in TICKERS:
                try:
                    items = provider.fetch_for_ticker(ticker)
                except ProviderRateLimited as exc:
                    # IP-level limit: the rest of this provider's pass is doomed too;
                    # tomorrow's run covers the gap (overlapping windows + URL dedup)
                    logger.warning("%s: %s — deferring rest of pass", provider.name, exc)
                    break
                except Exception:
                    logger.exception("%s news fetch failed for %s", provider.name, ticker)
                    continue
                total += store.upsert(items)
    return total


def update_fundamentals(db_path=DEFAULT_DB_PATH) -> int:
    client = EdgarClient()
    total = 0
    with FundamentalsStore(db_path) as store:
        for ticker in TICKERS:
            try:
                df = client.quarterly_facts(ticker)
            except Exception:
                logger.exception("fundamentals fetch failed for %s", ticker)
                continue
            total += store.upsert(df)
    return total


def daily_update(db_path=DEFAULT_DB_PATH) -> None:
    n_prices = update_prices(db_path)
    n_news = update_news(db_path)
    n_fundamentals = update_fundamentals(db_path)
    issues = run_report(db_path, as_of=date.today())
    logger.info(
        "daily update done: %d price rows, %d news items, %d fundamental facts,"
        " %d quality issues",
        n_prices, n_news, n_fundamentals, len(issues),
    )
    for issue in issues:
        logger.warning("quality: %s", issue)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    daily_update()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
