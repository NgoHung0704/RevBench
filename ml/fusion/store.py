"""Recommendation persistence (docs/ARCHITECTURE.md: serving layer)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH

from .schema import Recommendation

_SCHEMA = """
CREATE TABLE IF NOT EXISTS recommendations (
    ticker      VARCHAR   NOT NULL,
    as_of_date  DATE      NOT NULL,
    action      VARCHAR   NOT NULL,
    score       DOUBLE    NOT NULL,
    confidence  DOUBLE    NOT NULL,
    ml_proba    DOUBLE,
    components  VARCHAR   NOT NULL,
    rationale   VARCHAR,
    ingested_at TIMESTAMP NOT NULL,
    PRIMARY KEY (ticker, as_of_date)
);
"""


class RecommendationStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_SCHEMA)

    def upsert(self, recs: list[Recommendation]) -> int:
        now = datetime.now(UTC).replace(tzinfo=None)
        for r in recs:
            self.con.execute(
                "INSERT OR REPLACE INTO recommendations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    r.ticker, r.as_of_date, r.action, r.score, r.confidence,
                    r.ml_proba, json.dumps(r.components), r.rationale, now,
                ],
            )
        return len(recs)

    def load(self, ticker: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM recommendations"
        params: list = []
        if ticker is not None:
            query += " WHERE ticker = ?"
            params.append(ticker)
        query += " ORDER BY as_of_date, ticker"
        return self.con.execute(query, params).fetchdf()

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> RecommendationStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
