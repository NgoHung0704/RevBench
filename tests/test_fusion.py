import math

from ml.fusion.fuse import fuse
from ml.fusion.schema import FusionConfig, Recommendation
from ml.fusion.store import RecommendationStore

DAY = __import__("datetime").date(2026, 6, 11)


def test_ml_only_buy():
    r = fuse("AAPL", DAY, ml_proba=0.8, agent_signals={})
    assert r.action == "buy"
    assert math.isclose(r.score, 0.6, abs_tol=1e-9)  # (0.8-0.5)*2
    assert r.components == {"ml": 0.6}


def test_agents_only():
    r = fuse("AAPL", DAY, ml_proba=None, agent_signals={"news": (0.5, 1.0)})
    assert r.action == "buy"
    assert math.isclose(r.score, 0.5, abs_tol=1e-9)
    assert "ml" not in r.components


def test_disagreement_pulls_to_hold_and_kills_confidence():
    # ML bullish, agents bearish, equal weight -> net zero -> hold, low confidence
    r = fuse("AAPL", DAY, ml_proba=0.75, agent_signals={"news": (-0.5, 1.0)})
    assert r.action == "hold"
    assert abs(r.score) < 1e-9
    assert r.confidence == 0.0


def test_sell_threshold():
    r = fuse("AAPL", DAY, ml_proba=0.2, agent_signals={"technical": (-0.6, 0.8)})
    assert r.action == "sell"
    assert r.score < 0


def test_no_legs_is_neutral_hold():
    r = fuse("AAPL", DAY, ml_proba=None, agent_signals={})
    assert r.action == "hold"
    assert r.score == 0.0 and r.confidence == 0.0


def test_confidence_weighting_of_agents():
    # a high-confidence positive should dominate a low-confidence negative
    r = fuse("AAPL", DAY, ml_proba=None,
             agent_signals={"news": (1.0, 0.9), "technical": (-1.0, 0.1)})
    assert r.score > 0


def test_deterministic():
    a = fuse("AAPL", DAY, 0.7, {"news": (0.3, 0.6)})
    b = fuse("AAPL", DAY, 0.7, {"news": (0.3, 0.6)})
    assert a == b


def test_custom_thresholds():
    cfg = FusionConfig(buy_threshold=0.05, sell_threshold=-0.05)
    r = fuse("AAPL", DAY, ml_proba=0.55, agent_signals={}, config=cfg)  # ml_signal 0.1
    assert r.action == "buy"


def test_store_roundtrip(tmp_path):
    rec = Recommendation(
        ticker="AAPL", as_of_date=DAY, action="buy", score=0.4, confidence=0.7,
        ml_proba=0.6, components={"ml": 0.2, "news": 0.5}, rationale="Net bullish.",
    )
    with RecommendationStore(tmp_path / "t.duckdb") as store:
        assert store.upsert([rec]) == 1
        store.upsert([rec])  # idempotent on (ticker, as_of_date)
        df = store.load("AAPL")
        assert len(df) == 1
        assert df.iloc[0]["action"] == "buy"
        assert '"news"' in df.iloc[0]["components"]
