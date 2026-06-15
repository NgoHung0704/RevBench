import json
from datetime import date

from conftest import make_frame

from agents.store import AgentStore
from data_pipeline import scheduler
from data_pipeline.store import PriceStore
from ml.fusion.fuse import generate_recommendations
from ml.fusion.store import RecommendationStore

TICKERS = ("AAPL", "MSFT")


def populate(db, with_signals=True):
    with PriceStore(db) as ps:
        for i, t in enumerate(TICKERS):
            ps.upsert_daily(t, make_frame(420, seed=i), "yfinance")
    if not with_signals:
        return
    with AgentStore(db) as s:
        for t in TICKERS:
            for agent, sig in [("news", 0.3), ("technical", -0.2), ("fundamentals", 0.1)]:
                s.upsert_signal(
                    ticker=t, as_of_date=date(2026, 6, 11), agent=agent, signal=sig,
                    confidence=0.6, payload_json=json.dumps({"signal": sig}),
                    model="deepseek-v4-pro",
                )


def test_generate_recommendations_end_to_end(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    with AgentStore(db) as store:
        recs = generate_recommendations(db, store, TICKERS)
    assert len(recs) == 2
    for r in recs:
        assert "ml" in r.components  # ML leg present
        assert {"news", "technical", "fundamentals"} <= set(r.components)
        assert r.action in {"buy", "hold", "sell"}


def test_fusion_is_ml_only_without_agent_signals(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db, with_signals=False)
    with AgentStore(db) as store:
        recs = generate_recommendations(db, store, TICKERS)
    assert len(recs) == 2
    for r in recs:
        assert set(r.components) == {"ml"}  # no agents -> ML-only


def test_pipeline_skips_agents_runs_fusion(tmp_path, monkeypatch):
    """run_agents=False: no LLM calls, but fusion still produces ML-only recs."""
    db = tmp_path / "t.duckdb"
    populate(db, with_signals=False)
    monkeypatch.setattr(scheduler, "daily_update", lambda _db: None)  # no network

    scheduler.run_daily_pipeline(db_path=db, run_agents=False)

    with RecommendationStore(db) as rstore:
        recs = rstore.load()
    assert len(recs) == 2
    with AgentStore(db) as store:
        assert store.spent_today_usd() == 0.0  # agents never ran
