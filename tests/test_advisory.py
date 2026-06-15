import json
from datetime import date

from conftest import make_frame

from agents.advisory import enrich_recommendations
from agents.config import AgentSettings
from agents.context import risk_stats
from agents.guard import CostGuard
from agents.llm import LLMClient
from agents.orchestrator import _UsageTracker
from agents.store import AgentStore
from agents.testing import ADVISORY_CYCLE, FakeTransport
from ml.fusion.schema import Recommendation
from ml.fusion.store import RecommendationStore

SETTINGS = AgentSettings(deepseek_api_key="test", _env_file=None)
DAY = date(2026, 6, 11)


def _base_rec(ticker="AAPL"):
    return Recommendation(
        ticker=ticker, as_of_date=DAY, action="buy", score=0.3, confidence=0.5,
        ml_proba=0.6, components={"ml": 0.2, "technical": 0.4}, rationale="Net bullish.",
    )


def test_risk_stats_reasonable():
    stats = risk_stats(make_frame(300, seed=1))
    assert stats["ann_vol"] > 0
    assert stats["max_drawdown_1y"] <= 0
    assert "ret_21" in stats


def test_update_advice_roundtrip(tmp_path):
    from agents.schemas import RiskOutput, StrategistOutput

    with RecommendationStore(tmp_path / "t.duckdb") as store:
        store.upsert([_base_rec()])
        store.update_advice(
            "AAPL", DAY,
            RiskOutput(risk_level="high", max_position_pct=3.0, stop_loss_pct=10.0,
                       risk_flags=["earnings soon"], rationale="x"),
            StrategistOutput(thesis="Cautious buy.", counterarguments=["weak ML"],
                             conviction="medium"),
        )
        row = store.load("AAPL").iloc[0]
        assert row["risk_level"] == "high"
        assert row["max_position_pct"] == 3.0
        assert row["thesis"] == "Cautious buy."
        assert json.loads(row["counterarguments"]) == ["weak ML"]


def test_enrich_recommendations_fills_advice(tmp_path):
    db = tmp_path / "t.duckdb"
    recs = [_base_rec("AAPL"), _base_rec("MSFT")]
    frames = {"AAPL": make_frame(300, seed=1), "MSFT": make_frame(300, seed=2)}
    with RecommendationStore(db) as rstore:
        rstore.upsert(recs)
    with AgentStore(db) as store, RecommendationStore(db) as rstore:
        tracker = _UsageTracker(store)
        client = LLMClient(SETTINGS, transport=FakeTransport(ADVISORY_CYCLE), on_usage=tracker)
        n = enrich_recommendations(db, recs, client, rstore, CostGuard(store, 1.0),
                                   tracker, frames=frames)
        assert n == 2
        out = rstore.load()
        assert (out["risk_level"] == "moderate").all()
        assert out["thesis"].notna().all()


def test_enrich_skips_on_bad_output(tmp_path):
    db = tmp_path / "t.duckdb"
    recs = [_base_rec("AAPL")]
    frames = {"AAPL": make_frame(300, seed=1)}
    with RecommendationStore(db) as rstore:
        rstore.upsert(recs)
    with AgentStore(db) as store, RecommendationStore(db) as rstore:
        tracker = _UsageTracker(store)
        # both attempts return junk -> SchemaValidationError -> skipped, base rec intact
        client = LLMClient(SETTINGS, transport=FakeTransport(["not json", "still not"]),
                           on_usage=tracker)
        n = enrich_recommendations(db, recs, client, rstore, CostGuard(store, 1.0),
                                   tracker, frames=frames)
        assert n == 0
        row = rstore.load("AAPL").iloc[0]
        assert row["risk_level"] is None or (isinstance(row["risk_level"], float))  # unset
        assert row["action"] == "buy"  # base recommendation untouched


def test_enrich_respects_budget(tmp_path):
    from agents.llm import CallUsage

    db = tmp_path / "t.duckdb"
    recs = [_base_rec("AAPL"), _base_rec("MSFT")]
    frames = {"AAPL": make_frame(300, seed=1), "MSFT": make_frame(300, seed=2)}
    with RecommendationStore(db) as rstore:
        rstore.upsert(recs)
    with AgentStore(db) as store, RecommendationStore(db) as rstore:
        tracker = _UsageTracker(store)
        client = LLMClient(
            SETTINGS, transport=FakeTransport(ADVISORY_CYCLE),
            on_usage=lambda u: store.record_usage("x", CallUsage(u.model, 0, 0, 0, 99.0)),
        )
        n = enrich_recommendations(db, recs, client, rstore, CostGuard(store, 1.0),
                                   tracker, frames=frames)
        assert n <= 1  # budget blown after the first ticker's calls
