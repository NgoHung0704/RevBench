"""Agent-side persistence: usage ledger (feeds the cost guard) + sentiment scores.

news_sentiment is derived data: available_at = when WE computed it (now), not
when the article was published — an agent score cannot time-travel into a
backtest before the moment it existed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH

from .llm import CallUsage

_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_usage (
    ts                TIMESTAMP NOT NULL,
    agent             VARCHAR   NOT NULL,
    model             VARCHAR   NOT NULL,
    prompt_tokens     BIGINT    NOT NULL,
    completion_tokens BIGINT    NOT NULL,
    cached_tokens     BIGINT    NOT NULL,
    cost_usd          DOUBLE    NOT NULL
);
CREATE TABLE IF NOT EXISTS news_sentiment (
    news_id      VARCHAR   NOT NULL,
    ticker       VARCHAR   NOT NULL,
    score        DOUBLE    NOT NULL,
    confidence   DOUBLE    NOT NULL,
    event_type   VARCHAR   NOT NULL,
    summary      VARCHAR,
    model        VARCHAR   NOT NULL,
    available_at TIMESTAMP NOT NULL,
    ingested_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (news_id, ticker)
);
"""


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AgentStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_SCHEMA)

    # --- usage ledger ---

    def record_usage(self, agent: str, usage: CallUsage) -> None:
        self.con.execute(
            "INSERT INTO agent_usage VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                _utcnow(), agent, usage.model, usage.prompt_tokens,
                usage.completion_tokens, usage.cached_tokens, usage.cost_usd,
            ],
        )

    def spent_today_usd(self) -> float:
        value = self.con.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_usage"
            " WHERE ts >= CAST(CURRENT_DATE AS TIMESTAMP)"
        ).fetchone()[0]
        return float(value)

    # --- sentiment ---

    def unscored_news(self, limit: int | None = None) -> pd.DataFrame:
        query = """
            SELECT n.id, n.ticker, n.title, n.summary, n.source, n.published_at
            FROM news n
            LEFT JOIN news_sentiment s ON s.news_id = n.id AND s.ticker = n.ticker
            WHERE s.news_id IS NULL
            ORDER BY n.published_at DESC
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return self.con.execute(query).fetchdf()

    def upsert_sentiment(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        now = _utcnow()
        frame = pd.DataFrame(rows)
        frame["available_at"] = now
        frame["ingested_at"] = now
        self.con.register("_sent_batch", frame)
        self.con.execute(
            """
            INSERT OR REPLACE INTO news_sentiment
            SELECT news_id, ticker, score, confidence, event_type, summary, model,
                   available_at, ingested_at
            FROM _sent_batch
            """
        )
        self.con.unregister("_sent_batch")
        return len(frame)

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> AgentStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
