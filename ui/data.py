"""Read-only data access for the UI (docs/ARCHITECTURE.md: serving reads only).

Opens DuckDB read-only so the dashboard never contends with a writing job, and
never triggers an LLM call — it only surfaces what the batch already computed.
Phase 6's FastAPI backend can promote these queries into a service layer.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH
from data_pipeline.universe import STOCK_BY_TICKER


def _connect(db: str | Path) -> duckdb.DuckDBPyConnection:
    # read_only avoids locking against the scheduler; run the UI when no job writes.
    return duckdb.connect(str(db), read_only=True)


def _ready(db: str | Path) -> bool:
    # read_only on a non-existent file raises; the UI may start before any data.
    return Path(db).exists()


def _table_exists(con, name: str) -> bool:
    return bool(
        con.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?", [name]
        ).fetchone()
    )


def available_tickers(db: str | Path = DEFAULT_DB_PATH) -> list[str]:
    if not _ready(db):
        return []
    with _connect(db) as con:
        if not _table_exists(con, "prices"):
            return []
        rows = con.execute("SELECT DISTINCT ticker FROM prices ORDER BY ticker").fetchall()
    return [r[0] for r in rows]


def latest_signal_matrix(db: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Wide table (index=ticker, columns=agent) of each ticker's most recent signal."""
    if not _ready(db):
        return pd.DataFrame()
    with _connect(db) as con:
        if not _table_exists(con, "agent_signals"):
            return pd.DataFrame()
        df = con.execute(
            """
            WITH latest AS (
                SELECT ticker, MAX(as_of_date) AS md FROM agent_signals GROUP BY ticker
            )
            SELECT a.ticker, a.agent, a.signal
            FROM agent_signals a
            JOIN latest l ON a.ticker = l.ticker AND a.as_of_date = l.md
            """
        ).fetchdf()
    if df.empty:
        return df
    return df.pivot_table(index="ticker", columns="agent", values="signal")


def price_history(
    db: str | Path = DEFAULT_DB_PATH, ticker: str = "", days: int = 180
) -> pd.DataFrame:
    with _connect(db) as con:
        df = con.execute(
            """
            SELECT date, open, high, low, close, adj_close, volume
            FROM prices WHERE ticker = ? ORDER BY date DESC LIMIT ?
            """,
            [ticker, int(days)],
        ).fetchdf()
    return df.sort_values("date").set_index("date")


def ticker_signals(db: str | Path = DEFAULT_DB_PATH, ticker: str = "") -> list[dict]:
    """Latest agent_signals rows for one ticker, payload parsed."""
    with _connect(db) as con:
        if not _table_exists(con, "agent_signals"):
            return []
        df = con.execute(
            """
            SELECT agent, signal, confidence, payload, as_of_date
            FROM agent_signals
            WHERE ticker = ? AND as_of_date = (
                SELECT MAX(as_of_date) FROM agent_signals WHERE ticker = ?
            )
            ORDER BY agent
            """,
            [ticker, ticker],
        ).fetchdf()
    out = []
    for row in df.itertuples():
        out.append(
            {
                "agent": row.agent,
                "signal": float(row.signal),
                "confidence": float(row.confidence),
                "as_of_date": row.as_of_date,
                "payload": json.loads(row.payload),
            }
        )
    return out


def ticker_news(
    db: str | Path = DEFAULT_DB_PATH, ticker: str = "", limit: int = 20
) -> pd.DataFrame:
    with _connect(db) as con:
        if not _table_exists(con, "news_sentiment"):
            return pd.DataFrame()
        return con.execute(
            """
            SELECT n.published_at, n.title, s.score, s.confidence, s.event_type
            FROM news_sentiment s
            JOIN news n ON n.id = s.news_id AND n.ticker = s.ticker
            WHERE s.ticker = ?
            ORDER BY n.published_at DESC
            LIMIT ?
            """,
            [ticker, int(limit)],
        ).fetchdf()


def ticker_fundamentals(
    db: str | Path = DEFAULT_DB_PATH, ticker: str = "", per_metric: int = 6
) -> pd.DataFrame:
    with _connect(db) as con:
        if not _table_exists(con, "fundamentals"):
            return pd.DataFrame()
        df = con.execute(
            """
            SELECT metric, period_end, value, form, filed
            FROM fundamentals WHERE ticker = ? ORDER BY metric, period_end
            """,
            [ticker],
        ).fetchdf()
    if df.empty:
        return df
    return df.groupby("metric", group_keys=False).tail(per_metric)


def latest_recommendations(db: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """One row per ticker at its most recent as_of_date (action, score, confidence)."""
    if not _ready(db):
        return pd.DataFrame()
    with _connect(db) as con:
        if not _table_exists(con, "recommendations"):
            return pd.DataFrame()
        return con.execute(
            """
            SELECT r.ticker, r.action, r.score, r.confidence, r.ml_proba, r.as_of_date
            FROM recommendations r
            JOIN (SELECT ticker, MAX(as_of_date) md FROM recommendations GROUP BY ticker) l
              ON r.ticker = l.ticker AND r.as_of_date = l.md
            ORDER BY r.score DESC
            """
        ).fetchdf()


def ticker_recommendation(db: str | Path = DEFAULT_DB_PATH, ticker: str = "") -> dict | None:
    if not _ready(db):
        return None
    with _connect(db) as con:
        if not _table_exists(con, "recommendations"):
            return None
        df = con.execute(
            """
            SELECT action, score, confidence, ml_proba, rationale, as_of_date,
                   risk_level, max_position_pct, stop_loss_pct, risk_flags,
                   thesis, counterarguments, conviction
            FROM recommendations WHERE ticker = ?
            ORDER BY as_of_date DESC LIMIT 1
            """,
            [ticker],
        ).fetchdf()
    if df.empty:
        return None
    row = df.iloc[0]

    def _jsonlist(v):
        return json.loads(v) if isinstance(v, str) and v else []

    def _opt(v):
        return None if pd.isna(v) else v

    return {
        "action": row["action"], "score": float(row["score"]),
        "confidence": float(row["confidence"]),
        "ml_proba": None if pd.isna(row["ml_proba"]) else float(row["ml_proba"]),
        "rationale": row["rationale"], "as_of_date": row["as_of_date"],
        "risk_level": _opt(row["risk_level"]),
        "max_position_pct": _opt(row["max_position_pct"]),
        "stop_loss_pct": _opt(row["stop_loss_pct"]),
        "risk_flags": _jsonlist(row["risk_flags"]),
        "thesis": _opt(row["thesis"]),
        "counterarguments": _jsonlist(row["counterarguments"]),
        "conviction": _opt(row["conviction"]),
    }


def cost_summary(db: str | Path = DEFAULT_DB_PATH) -> dict:
    if not _ready(db):
        return {"today": 0.0, "total": 0.0, "calls": 0}
    with _connect(db) as con:
        if not _table_exists(con, "agent_usage"):
            return {"today": 0.0, "total": 0.0, "calls": 0}
        today = con.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_usage"
            " WHERE ts >= CAST(CURRENT_DATE AS TIMESTAMP)"
        ).fetchone()[0]
        total, calls = con.execute(
            "SELECT COALESCE(SUM(cost_usd), 0), COUNT(*) FROM agent_usage"
        ).fetchone()
    return {"today": float(today), "total": float(total), "calls": int(calls)}


def stock_name(ticker: str) -> str:
    stock = STOCK_BY_TICKER.get(ticker)
    return stock.name if stock else ticker


def sector(ticker: str) -> str:
    stock = STOCK_BY_TICKER.get(ticker)
    return stock.sector if stock else ""
