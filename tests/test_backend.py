import json
from datetime import date, datetime

import pandas as pd
import pytest
from conftest import make_frame

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from agents.schemas import RiskOutput, StrategistOutput  # noqa: E402
from agents.store import AgentStore  # noqa: E402
from data_pipeline.news.base import NewsItem, item_id  # noqa: E402
from data_pipeline.store import FundamentalsStore, NewsStore, PriceStore  # noqa: E402
from ml.fusion.schema import Recommendation  # noqa: E402
from ml.fusion.store import RecommendationStore  # noqa: E402

DAY = date(2026, 6, 11)


def _facts() -> pd.DataFrame:
    rows = []
    for i, end in enumerate(["2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"]):
        e = pd.Timestamp(end)
        rows.append({
            "ticker": "AAPL", "metric": "revenue", "period_start": e - pd.Timedelta(days=90),
            "period_end": e, "value": 90_000_000_000 + i * 3e9, "unit": "USD", "form": "10-Q",
            "fy": 2025, "fp": f"Q{i}", "accn": f"a-{i}", "filed": e + pd.Timedelta(days=20),
            "available_at": e + pd.Timedelta(days=21),
        })
    return pd.DataFrame(rows)


def populate(db):
    with PriceStore(db) as ps:
        ps.upsert_daily("AAPL", make_frame(200, seed=1), "yfinance")

    now = datetime.now()
    url = "https://ex.com/AAPL/0"
    with NewsStore(db) as ns:
        ns.upsert([NewsItem(id=item_id(url), ticker="AAPL", title="Apple ships new chip",
                            summary="s", url=url, source="test",
                            published_at=now, available_at=now)])
    with AgentStore(db) as ags:
        ags.upsert_sentiment([{"news_id": item_id(url), "ticker": "AAPL", "score": 0.5,
                               "confidence": 0.8, "event_type": "product", "summary": "s",
                               "model": "test"}])
        payloads = {
            "news": {"summary": "Constructive coverage.", "key_events": ["new chip"],
                     "catalysts": ["earnings"]},
            "technical": {"regime": "uptrend", "rationale": "Above MA200."},
            "fundamentals": {"valuation_view": "fair", "growth_view": "steady",
                             "red_flags": [], "rationale": "Stable."},
        }
        for agent, sig in [("news", 0.3), ("technical", 0.4), ("fundamentals", -0.1)]:
            ags.upsert_signal("AAPL", DAY, agent, sig, 0.6,
                              json.dumps(payloads[agent]), "deepseek-v4-pro")
    with FundamentalsStore(db) as fs:
        fs.upsert(_facts())
    with RecommendationStore(db) as rs:
        rs.upsert([Recommendation("AAPL", DAY, "buy", 0.3, 0.5, 0.6,
                                  {"ml": 0.2, "news": 0.3, "technical": 0.4, "fundamentals": -0.1},
                                  "Net bullish.")])
        rs.update_advice("AAPL", DAY,
                         RiskOutput(risk_level="moderate", max_position_pct=5.0, stop_loss_pct=8.0,
                                    risk_flags=["elevated volatility"], rationale="x"),
                         StrategistOutput(thesis="A cautious buy on momentum.",
                                          counterarguments=["thin ML edge"], conviction="medium"))


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "t.duckdb"
    populate(db)
    monkeypatch.setenv("REVBENCH_DB", str(db))
    from backend.app.main import app

    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_universe(client):
    r = client.get("/api/universe")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    item = data[0]
    assert item["stock"]["ticker"] == "AAPL"
    assert item["rec"]["action"] == "buy"
    assert item["rec"]["components"]["technical"] == 0.4
    assert len(item["prices"]) > 10 and item["lastClose"] > 0


def test_ticker_detail(client):
    r = client.get("/api/tickers/aapl")  # case-insensitive
    assert r.status_code == 200
    d = r.json()
    assert d["rec"]["thesis"] == "A cautious buy on momentum."
    assert d["rec"]["riskLevel"] == "moderate"
    assert {s["agent"] for s in d["signals"]} == {"news", "technical", "fundamentals"}
    tech = next(s for s in d["signals"] if s["agent"] == "technical")
    assert tech["regime"] == "uptrend"
    assert len(d["news"]) == 1
    assert any(f["metric"] == "revenue" for f in d["fundamentals"])
    assert len(d["prices"]) > 100


def test_ticker_404(client):
    assert client.get("/api/tickers/ZZZZ").status_code == 404
