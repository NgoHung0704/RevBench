"""DuckDB storage — prices + news (docs/DECISIONS.md D2).

Point-in-time rule (CLAUDE.md hard rule #1): every record carries `available_at`,
the moment the information could have been known. Backtests may only read rows
with available_at <= t. All timestamps are stored naive-UTC.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd

from .altdata.base import AltDataPoint
from .news.base import NewsItem

# Single source of truth for the DB location. REVBENCH_DB lets the deployment
# point every reader AND writer at the mounted volume (docker-compose); unset,
# it falls back to the repo-relative path used for local development. The API
# resolves the same env var (backend/app/config.py), so both agree.
DEFAULT_DB_PATH = Path(os.environ.get("REVBENCH_DB", "data/revbench.duckdb"))

# Daily US bars become known at the NYSE close, 16:00 New York time.
# We store a constant 21:00 UTC (the EDT close; 22:00 UTC in winter). Conservative
# enough for a 5-day horizon — revisit only if we ever go intraday.
US_CLOSE_UTC = timedelta(hours=21)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    ticker       VARCHAR   NOT NULL,
    date         DATE      NOT NULL,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    adj_close    DOUBLE,
    volume       BIGINT,
    available_at TIMESTAMP NOT NULL,
    ingested_at  TIMESTAMP NOT NULL,
    source       VARCHAR   NOT NULL,
    PRIMARY KEY (ticker, date, source)
);
"""


class PriceStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_SCHEMA)

    def upsert_daily(self, ticker: str, df: pd.DataFrame, source: str) -> int:
        """Insert-or-replace daily bars (idempotent on ticker/date/source)."""
        rows = df.reset_index()
        rows["ticker"] = ticker
        rows["available_at"] = pd.to_datetime(rows["date"]) + US_CLOSE_UTC
        rows["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
        rows["source"] = source
        self.con.register("_batch", rows)
        self.con.execute(
            """
            INSERT OR REPLACE INTO prices
            SELECT ticker, date, open, high, low, close, adj_close, volume,
                   available_at, ingested_at, source
            FROM _batch
            """
        )
        self.con.unregister("_batch")
        return len(rows)

    def load_daily(self, ticker: str, source: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM prices WHERE ticker = ?"
        params: list = [ticker]
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY date"
        df = self.con.execute(query, params).fetchdf()
        return df.set_index("date")

    def coverage(self) -> pd.DataFrame:
        return self.con.execute(
            """
            SELECT ticker, source, COUNT(*) AS rows,
                   MIN(date) AS first_date, MAX(date) AS last_date
            FROM prices GROUP BY ticker, source ORDER BY ticker
            """
        ).fetchdf()

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> PriceStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_NEWS_SCHEMA = """
CREATE TABLE IF NOT EXISTS news (
    id           VARCHAR   NOT NULL,
    ticker       VARCHAR   NOT NULL,
    title        VARCHAR   NOT NULL,
    summary      VARCHAR,
    url          VARCHAR   NOT NULL,
    source       VARCHAR   NOT NULL,
    published_at TIMESTAMP NOT NULL,
    available_at TIMESTAMP NOT NULL,
    ingested_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (id, ticker)
);
"""


class NewsStore:
    """News articles tagged per ticker; one article may appear under several tickers."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_NEWS_SCHEMA)

    def upsert(self, items: list[NewsItem]) -> int:
        if not items:
            return 0
        rows = pd.DataFrame([item.model_dump() for item in items])
        # a feed can repeat the same URL within one fetch
        rows = rows.drop_duplicates(subset=["id", "ticker"], keep="last")
        rows["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
        self.con.register("_news_batch", rows)
        self.con.execute(
            """
            INSERT OR REPLACE INTO news
            SELECT id, ticker, title, summary, url, source,
                   published_at, available_at, ingested_at
            FROM _news_batch
            """
        )
        self.con.unregister("_news_batch")
        return len(rows)

    def load(self, ticker: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM news"
        params: list = []
        if ticker is not None:
            query += " WHERE ticker = ?"
            params.append(ticker)
        query += " ORDER BY published_at"
        return self.con.execute(query, params).fetchdf()

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> NewsStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_FUNDAMENTALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS fundamentals (
    ticker       VARCHAR   NOT NULL,
    metric       VARCHAR   NOT NULL,
    period_start DATE,
    period_end   DATE      NOT NULL,
    value        DOUBLE    NOT NULL,
    unit         VARCHAR   NOT NULL,
    form         VARCHAR   NOT NULL,
    fy           BIGINT,
    fp           VARCHAR,
    accn         VARCHAR   NOT NULL,
    filed        DATE      NOT NULL,
    available_at TIMESTAMP NOT NULL,
    ingested_at  TIMESTAMP NOT NULL,
    -- period_start in the PK: a 10-Q reports a 3-month and a YTD value for the
    -- same (period_end, accn), differing only in start (docs/REVISIT.md R4).
    PRIMARY KEY (ticker, metric, period_start, period_end, accn)
);
"""


class FundamentalsStore:
    """XBRL facts from EDGAR; one row per (metric, period, filing) — amendments kept."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_FUNDAMENTALS_SCHEMA)

    def upsert(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        rows = df.copy()
        rows["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
        self.con.register("_fund_batch", rows)
        self.con.execute(
            """
            INSERT OR REPLACE INTO fundamentals
            SELECT ticker, metric,
                   CAST(period_start AS DATE), CAST(period_end AS DATE),
                   value, unit, form, fy, fp, accn,
                   CAST(filed AS DATE), available_at, ingested_at
            FROM _fund_batch
            """
        )
        self.con.unregister("_fund_batch")
        return len(rows)

    def load(self, ticker: str, metric: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM fundamentals WHERE ticker = ?"
        params: list = [ticker]
        if metric is not None:
            query += " AND metric = ?"
            params.append(metric)
        query += " ORDER BY metric, period_end, filed"
        return self.con.execute(query, params).fetchdf()

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> FundamentalsStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_ALTDATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS altdata (
    source       VARCHAR   NOT NULL,
    ticker       VARCHAR   NOT NULL,
    date         DATE      NOT NULL,
    value        DOUBLE    NOT NULL,
    available_at TIMESTAMP NOT NULL,
    ingested_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (source, ticker, date)
);
"""


class AltDataStore:
    """Generic alternative-data series (Google Trends, pageviews, …)."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(path))
        self.con.execute(_ALTDATA_SCHEMA)

    def upsert(self, points: list[AltDataPoint]) -> int:
        if not points:
            return 0
        rows = pd.DataFrame([p.model_dump() for p in points])
        rows = rows.drop_duplicates(subset=["source", "ticker", "date"], keep="last")
        rows["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
        self.con.register("_alt_batch", rows)
        self.con.execute(
            """
            INSERT OR REPLACE INTO altdata
            SELECT source, ticker, CAST(date AS DATE), value, available_at, ingested_at
            FROM _alt_batch
            """
        )
        self.con.unregister("_alt_batch")
        return len(rows)

    def load(self, source: str, ticker: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM altdata WHERE source = ?"
        params: list = [source]
        if ticker is not None:
            query += " AND ticker = ?"
            params.append(ticker)
        query += " ORDER BY ticker, date"
        return self.con.execute(query, params).fetchdf()

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> AltDataStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
