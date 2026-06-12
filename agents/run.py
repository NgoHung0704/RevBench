"""Agent runner CLI (docs/PLAN.md Phase 3).

Usage:
    python -m agents.run --task sentiment --limit 20
    python -m agents.run --task sentiment --dry-run --limit 3   # no key, no cost,
                                                                # canned responses,
                                                                # nothing persisted

Live runs record every call in the agent_usage ledger and stop hard at
AGENT_DAILY_BUDGET_USD.
"""

import argparse
import logging

from data_pipeline.store import DEFAULT_DB_PATH

from .config import AgentSettings
from .guard import CostGuard
from .llm import LLMClient
from .roster.sentiment import AGENT_NAME, score_unscored_news
from .store import AgentStore
from .testing import FakeTransport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, choices=["sentiment"])
    parser.add_argument("--limit", type=int, default=None, help="max records this run")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="fake transport, no API key needed, nothing persisted",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="DuckDB path")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = AgentSettings()

    with AgentStore(args.db) as store:
        guard = CostGuard(store, settings.agent_daily_budget_usd)
        if args.dry_run:
            client = LLMClient(settings=settings, transport=FakeTransport())
        else:
            spent: list[float] = []
            client = LLMClient(
                settings=settings,
                on_usage=lambda u: (store.record_usage(AGENT_NAME, u), spent.append(u.cost_usd)),
            )

        run = score_unscored_news(
            client, store, guard, limit=args.limit, persist=not args.dry_run
        )

        mode = "DRY-RUN (nothing persisted)" if args.dry_run else "LIVE"
        print(f"\n[{mode}] scored={run.scored} skipped={run.skipped}"
              f" stopped_by_budget={run.stopped_by_budget}")
        if not args.dry_run:
            print(f"spent this run: ${sum(spent):.4f} | spent today: ${store.spent_today_usd():.4f}"
                  f" / budget ${settings.agent_daily_budget_usd:.2f}")
        for s in run.samples:
            print(f"  {s['ticker']:>5} {s['score']:+.2f} ({s['event_type']},"
                  f" conf {s['confidence']:.2f}) {s['title'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
