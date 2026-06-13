from datetime import datetime, timedelta

import pandas as pd
import pytest
from conftest import make_frame

from agents.config import AgentSettings
from agents.guard import CostGuard
from agents.llm import CallUsage, LLMClient
from agents.orchestrator import _build_contexts, _UsageTracker, run_signals
from agents.store import AgentStore
from agents.testing import REASONING_CYCLE, FakeTransport
from data_pipeline.fundamentals.fetch import FundamentalsStore
from data_pipeline.news.base import NewsItem, item_id
from data_pipeline.store import NewsStore, PriceStore

SETTINGS = AgentSettings(deepseek_api_key="test", _env_file=None)
TICKERS = ("AAPL", "MSFT")


def _facts(tickers, available_at: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for t in tickers:
        for q, end in enumerate(["2024-03-31", "2024-06-30"]):
            rows.append(
                {
                    "ticker": t, "metric": "revenue",
                    "period_start": pd.Timestamp(end) - pd.Timedelta(days=90),
                    "period_end": pd.Timestamp(end), "value": 1000.0 + q * 100,
                    "unit": "USD", "form": "10-Q", "fy": 2024, "fp": f"Q{q+1}",
                    "accn": f"{t}-{q}", "filed": pd.Timestamp(end) + pd.Timedelta(days=20),
                    "available_at": available_at,
                }
            )
    return pd.DataFrame(rows)


def populate(db_path, tickers=TICKERS, n_days=420):
    with PriceStore(db_path) as ps:
        for i, t in enumerate(tickers):
            ps.upsert_daily(t, make_frame(n_days, seed=i), "yfinance")

    now = datetime.now()
    items, rows = [], []
    for t in tickers:
        for j in range(3):
            url = f"https://ex.com/{t}/{j}"
            items.append(
                NewsItem(
                    id=item_id(url), ticker=t, title=f"{t} headline {j}", summary="s",
                    url=url, source="test",
                    published_at=now - timedelta(days=1), available_at=now - timedelta(days=1),
                )
            )
            rows.append(
                {
                    "news_id": item_id(url), "ticker": t, "score": 0.1, "confidence": 0.5,
                    "event_type": "other", "summary": "s", "model": "test",
                }
            )
    with NewsStore(db_path) as ns:
        ns.upsert(items)
    with AgentStore(db_path) as ags:
        ags.upsert_sentiment(rows)
    with FundamentalsStore(db_path) as fs:
        fs.upsert(_facts(tickers, available_at=pd.Timestamp("2024-07-20")))


def fake_client() -> LLMClient:
    return LLMClient(settings=SETTINGS, transport=FakeTransport(REASONING_CYCLE))


def test_run_signals_stores_one_row_per_ticker_agent(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    with AgentStore(db) as store:
        tracker = _UsageTracker(store)
        run = run_signals(fake_client(), store, CostGuard(store, 1.0), tracker, TICKERS, db)
        assert len(run.results) == 2
        assert all(set(r.signals) == {"news", "technical", "fundamentals"} for r in run.results)
        signals = store.load_signals()
        assert len(signals) == 6  # 2 tickers x 3 agents
        assert set(signals["agent"]) == {"news", "technical", "fundamentals"}


def test_dry_run_persists_nothing(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    with AgentStore(db) as store:
        tracker = _UsageTracker(store)
        run = run_signals(
            fake_client(), store, CostGuard(store, 1.0), tracker, TICKERS, db, persist=False
        )
        assert len(run.results) == 2
        assert len(store.load_signals()) == 0


def test_budget_stops_run(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    with AgentStore(db) as store:
        tracker = _UsageTracker(store)
        client = LLMClient(
            settings=SETTINGS,
            transport=FakeTransport(REASONING_CYCLE),
            on_usage=lambda u: store.record_usage(
                "x", CallUsage(u.model, u.prompt_tokens, u.completion_tokens, 0, 99.0)
            ),
        )
        run = run_signals(client, store, CostGuard(store, 1.0), tracker, TICKERS, db)
        assert run.stopped_by_budget
        # first agent of the first ticker runs, then the budget blocks the rest
        assert len(store.load_signals()) <= 1


def test_fundamentals_point_in_time_excludes_future(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    # a fact filed in 2099 must never appear in context built as of 2024
    future = _facts(("AAPL",), available_at=pd.Timestamp("2099-01-01"))
    future["value"] = 999999.0
    future["accn"] = "FUTURE"
    with FundamentalsStore(db) as fs:
        fs.upsert(future)

    from ml.data import load_frames

    frames = load_frames(db, ("AAPL",))
    as_of = frames["AAPL"].index.max()
    with AgentStore(db) as store, FundamentalsStore(db) as fs:
        ctx = _build_contexts("AAPL", frames, fs, store, as_of)
    assert "999,999" not in ctx["fundamentals"]  # future fact excluded


@pytest.mark.integration
def test_real_orchestrator_one_ticker():
    """Live smoke test against DeepSeek — needs DEEPSEEK_API_KEY and local data."""
    settings = AgentSettings()
    with AgentStore() as store:
        tracker = _UsageTracker(store)
        client = LLMClient(settings=settings, on_usage=tracker)
        run = run_signals(client, store, CostGuard(store, 1.0), tracker, ("AAPL",))
        assert run.results and set(run.results[0].signals) <= {
            "news", "technical", "fundamentals"
        }
