"""Sentiment Agent (docs/AGENTS.md): bulk-scores news on deepseek-v4-flash.

Reads unscored articles from the news table, writes one row per (article,
ticker) into news_sentiment. A record whose output fails validation twice is
skipped and logged — never retried in a loop, never written half-parsed.
"""

import logging
from dataclasses import dataclass, field

from ..guard import BudgetExceededError, CostGuard
from ..llm import LLMClient, SchemaValidationError
from ..prompts.sentiment import SENTIMENT_SYSTEM
from ..schemas import SentimentOutput
from ..store import AgentStore

logger = logging.getLogger("revbench.agents.sentiment")

AGENT_NAME = "sentiment"
MAX_SUMMARY_CHARS = 1500  # cap pasted article text; titles carry most signal


@dataclass
class SentimentRun:
    scored: int = 0
    skipped: int = 0
    stopped_by_budget: bool = False
    samples: list[dict] = field(default_factory=list)


def build_user_message(ticker: str, title: str, summary: str) -> str:
    text = (summary or "").strip()[:MAX_SUMMARY_CHARS]
    return f"Ticker: {ticker}\nTitle: {title.strip()}\nSummary: {text or '(none)'}"


def score_unscored_news(
    client: LLMClient,
    store: AgentStore,
    guard: CostGuard,
    limit: int | None = None,
    persist: bool = True,
) -> SentimentRun:
    run = SentimentRun()
    pending = store.unscored_news(limit=limit)
    model = client.settings.sentiment_model

    for row in pending.itertuples():
        try:
            guard.check()
        except BudgetExceededError as exc:
            logger.warning("stopping: %s", exc)
            run.stopped_by_budget = True
            break
        try:
            out: SentimentOutput = client.complete_json(
                model=model,
                system=SENTIMENT_SYSTEM,
                user=build_user_message(row.ticker, row.title, row.summary),
                schema=SentimentOutput,
                max_tokens=300,
            )
        except SchemaValidationError as exc:
            logger.warning("skipping %s/%s: %s", row.id, row.ticker, exc)
            run.skipped += 1
            continue

        record = {
            "news_id": row.id,
            "ticker": row.ticker,
            "score": out.score,
            "confidence": out.confidence,
            "event_type": out.event_type,
            "summary": out.summary,
            "model": model,
        }
        if persist:
            store.upsert_sentiment([record])
        run.scored += 1
        if len(run.samples) < 5:
            run.samples.append({**record, "title": row.title})
    return run
