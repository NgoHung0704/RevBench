"""Agent runner CLI (docs/PLAN.md Phase 3).

Usage:
    python -m agents.run --task sentiment --limit 20
    python -m agents.run --task signals --tickers AAPL MSFT
    python -m agents.run --task signals --dry-run            # no key, no cost

`sentiment` bulk-scores news articles. `signals` runs the reasoning agents
(News / Technical / Fundamentals) per ticker and stores agent_signals.
Dry-run uses a fake transport: no API key, no cost, nothing persisted.
Live runs record usage in the agent_usage ledger and stop at the daily budget.
"""

import argparse
import logging

from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import TICKERS

from .config import AgentSettings
from .guard import CostGuard
from .llm import LLMClient
from .orchestrator import _UsageTracker, run_signals
from .roster.sentiment import AGENT_NAME, score_unscored_news
from .store import AgentStore
from .testing import REASONING_CYCLE, FakeTransport


def _run_sentiment(args, settings, store, guard) -> None:
    if args.dry_run:
        client = LLMClient(settings=settings, transport=FakeTransport())
    else:
        client = LLMClient(
            settings=settings, on_usage=lambda u: store.record_usage(AGENT_NAME, u)
        )
    run = score_unscored_news(client, store, guard, limit=args.limit, persist=not args.dry_run)
    mode = "DRY-RUN (nothing persisted)" if args.dry_run else "LIVE"
    print(f"\n[{mode}] scored={run.scored} skipped={run.skipped}"
          f" stopped_by_budget={run.stopped_by_budget}")
    if not args.dry_run:
        print(f"spent today: ${store.spent_today_usd():.4f}"
              f" / ${settings.agent_daily_budget_usd:.2f}")
    for s in run.samples:
        print(f"  {s['ticker']:>5} {s['score']:+.2f} ({s['event_type']}) {s['title'][:70]}")


def _run_signals(args, settings, store, guard) -> None:
    tickers = tuple(t.upper() for t in args.tickers) if args.tickers else TICKERS
    tracker = _UsageTracker(store)
    if args.dry_run:
        client = LLMClient(settings=settings, transport=FakeTransport(REASONING_CYCLE))
    else:
        client = LLMClient(settings=settings, on_usage=tracker)

    run = run_signals(
        client, store, guard, tracker, tickers=tickers, db_path=args.db,
        persist=not args.dry_run,
    )
    mode = "DRY-RUN (nothing persisted)" if args.dry_run else "LIVE"
    print(f"\n[{mode}] as_of={run.as_of_date} tickers={len(run.results)}"
          f" stopped_by_budget={run.stopped_by_budget}")
    if not args.dry_run:
        print(f"spent today: ${store.spent_today_usd():.4f}"
              f" / ${settings.agent_daily_budget_usd:.2f}")
    for res in run.results:
        sig = " ".join(f"{a}={v:+.2f}" for a, v in res.signals.items())
        fail = f" failed={res.failed}" if res.failed else ""
        print(f"  {res.ticker:>5}  {sig}{fail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, choices=["sentiment", "signals"])
    parser.add_argument("--tickers", nargs="+", metavar="T", help="subset (signals task)")
    parser.add_argument("--limit", type=int, default=None, help="max records (sentiment task)")
    parser.add_argument("--dry-run", action="store_true", help="fake transport, no key, no cost")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = AgentSettings()
    with AgentStore(args.db) as store:
        guard = CostGuard(store, settings.agent_daily_budget_usd)
        if args.task == "sentiment":
            _run_sentiment(args, settings, store, guard)
        else:
            _run_signals(args, settings, store, guard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
