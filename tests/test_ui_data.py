import json
from datetime import datetime

import pytest
from conftest import make_frame

from agents.schemas import RiskOutput, StrategistOutput
from agents.store import AgentStore
from data_pipeline.news.base import NewsItem, item_id
from data_pipeline.store import NewsStore, PriceStore
from ml.fusion.schema import Recommendation
from ml.fusion.store import RecommendationStore
from ui import data


def populate(db):
    with PriceStore(db) as ps:
        ps.upsert_daily("AAPL", make_frame(120, seed=1), "yfinance")
        ps.upsert_daily("MSFT", make_frame(120, seed=2), "yfinance")

    now = datetime.now()
    url = "https://ex.com/AAPL/0"
    with NewsStore(db) as ns:
        ns.upsert([
            NewsItem(
                id=item_id(url), ticker="AAPL", title="AAPL launches product",
                summary="s", url=url, source="test",
                published_at=now, available_at=now,
            )
        ])

    with AgentStore(db) as ags:
        ags.upsert_sentiment([{
            "news_id": item_id(url), "ticker": "AAPL", "score": 0.5, "confidence": 0.8,
            "event_type": "product", "summary": "s", "model": "test",
        }])
        ags.upsert_signal(
            ticker="AAPL", as_of_date=datetime(2026, 6, 11).date(), agent="technical",
            signal=0.4, confidence=0.6,
            payload_json=json.dumps({"regime": "uptrend", "signal": 0.4, "confidence": 0.6,
                                     "rationale": "Above MA200."}),
            model="deepseek-v4-pro",
        )
        ags.record_usage(
            "technical",
            type("U", (), {"model": "deepseek-v4-pro", "prompt_tokens": 100,
                           "completion_tokens": 50, "cached_tokens": 0, "cost_usd": 0.002})(),
        )

    with RecommendationStore(db) as rs:
        rs.upsert([Recommendation(
            ticker="AAPL", as_of_date=datetime(2026, 6, 11).date(), action="buy",
            score=0.3, confidence=0.5, ml_proba=0.6,
            components={"ml": 0.2, "technical": 0.4}, rationale="Net bullish.",
        )])
        rs.update_advice(
            "AAPL", datetime(2026, 6, 11).date(),
            RiskOutput(risk_level="moderate", max_position_pct=5.0, stop_loss_pct=8.0,
                       risk_flags=["elevated volatility"], rationale="x"),
            StrategistOutput(thesis="Mild bullish lean from technicals.",
                             counterarguments=["thin ML edge"], conviction="low"),
        )


def test_available_tickers(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    assert data.available_tickers(db) == ["AAPL", "MSFT"]


def test_missing_db_is_graceful(tmp_path):
    db = tmp_path / "nope.duckdb"  # never created
    assert data.available_tickers(db) == []
    assert data.latest_signal_matrix(db).empty
    assert data.cost_summary(db) == {"today": 0.0, "total": 0.0, "calls": 0}


def test_latest_signal_matrix(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    m = data.latest_signal_matrix(db)
    assert "technical" in m.columns
    assert m.loc["AAPL", "technical"] == 0.4


def test_price_history(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    px = data.price_history(db, "AAPL", days=30)
    assert len(px) == 30
    assert px.index.is_monotonic_increasing


def test_ticker_signals_parses_payload(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    sigs = data.ticker_signals(db, "AAPL")
    assert len(sigs) == 1
    assert sigs[0]["payload"]["regime"] == "uptrend"
    assert sigs[0]["signal"] == 0.4


def test_ticker_news(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    news = data.ticker_news(db, "AAPL")
    assert len(news) == 1
    assert news.iloc[0]["event_type"] == "product"


def test_cost_summary(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    cost = data.cost_summary(db)
    assert cost["calls"] == 1
    assert abs(cost["total"] - 0.002) < 1e-9


def test_signals_empty_for_unscored_ticker(tmp_path):
    db = tmp_path / "t.duckdb"
    populate(db)
    assert data.ticker_signals(db, "MSFT") == []


def test_streamlit_app_boots(tmp_path, monkeypatch):
    """Render the real app against a temp DB — catches Streamlit-API/render bugs
    a plain import test can't (it caught the matplotlib + width regressions)."""
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    db = tmp_path / "t.duckdb"
    populate(db)
    monkeypatch.setattr(data, "DEFAULT_DB_PATH", db)

    at = AppTest.from_file("ui/streamlit_app.py", default_timeout=30).run()
    assert not at.exception, at.exception
    at.radio[0].set_value("AAPL").run()  # ticker page with agent insights
    assert not at.exception, at.exception
