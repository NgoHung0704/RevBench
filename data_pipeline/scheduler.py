"""Daily pipeline + blocking scheduler (docs/DECISIONS.md D6, APScheduler).

This is the system's composition root: it wires the data layer, the agent layer,
and the fusion layer into one nightly run. The lower layers stay decoupled
(`jobs.py` knows nothing about agents); only this entry point composes them.

    python -m data_pipeline.scheduler --once   # run the full pipeline now
    python -m data_pipeline.scheduler          # schedule it (22:30 Europe/Paris)

NYSE closes 16:00 New York = 22:00 Paris, inside DeepSeek's off-peak window
(16:30-00:30 UTC, -50%), so the LLM steps run cheap. The whole pipeline is
resilient: data always runs; agents run only with a key and within budget;
fusion always runs (ML-only if no agent signals exist yet).
"""

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from agents.config import AgentSettings
from agents.guard import CostGuard
from agents.llm import LLMClient
from agents.orchestrator import _UsageTracker, run_signals
from agents.roster.sentiment import AGENT_NAME, score_unscored_news
from agents.store import AgentStore
from ml.fusion.fuse import generate_recommendations
from ml.fusion.store import RecommendationStore

from .jobs import daily_update
from .store import DEFAULT_DB_PATH
from .universe import TICKERS

logger = logging.getLogger("revbench.pipeline")


def _run_agents(db_path, settings: AgentSettings) -> None:
    """Sentiment + reasoning signals, sharing one daily budget guard."""
    with AgentStore(db_path) as store:
        guard = CostGuard(store, settings.agent_daily_budget_usd)

        sent_client = LLMClient(
            settings=settings, on_usage=lambda u: store.record_usage(AGENT_NAME, u)
        )
        sent = score_unscored_news(sent_client, store, guard)
        logger.info("sentiment: scored=%d skipped=%d", sent.scored, sent.skipped)

        tracker = _UsageTracker(store)
        sig_client = LLMClient(settings=settings, on_usage=tracker)
        sig = run_signals(sig_client, store, guard, tracker, TICKERS, db_path)
        logger.info("signals: %d tickers, $%.4f", len(sig.results), sig.cost_usd)


def _run_fusion(db_path) -> None:
    """Always runs — ML-only recommendations when no agent signals exist yet."""
    with AgentStore(db_path) as store:
        recs = generate_recommendations(db_path, store, TICKERS)
    if recs:
        with RecommendationStore(db_path) as rstore:
            rstore.upsert(recs)
    logger.info("fusion: %d recommendations stored", len(recs))


def run_daily_pipeline(db_path=DEFAULT_DB_PATH, run_agents: bool = True) -> None:
    daily_update(db_path)

    settings = AgentSettings()
    if run_agents and settings.deepseek_api_key:
        _run_agents(db_path, settings)
    else:
        logger.info("agents skipped (no DEEPSEEK_API_KEY or --no-agents); fusion is ML-only")

    _run_fusion(db_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="run the pipeline now and exit")
    parser.add_argument("--no-agents", action="store_true", help="data + ML fusion only")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    if args.once:
        run_daily_pipeline(run_agents=not args.no_agents)
        return 0

    scheduler = BlockingScheduler(timezone="Europe/Paris")
    scheduler.add_job(
        run_daily_pipeline, "cron", day_of_week="mon-fri", hour=22, minute=30,
        kwargs={"run_agents": not args.no_agents},
    )
    print("Scheduler running: daily pipeline at 22:30 Europe/Paris, Mon-Fri. Ctrl+C to stop.")
    scheduler.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
