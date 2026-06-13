import numpy as np
import pandas as pd

from agents.context import fundamentals_context, news_context, technical_context


def test_technical_context_formats_and_skips_nan():
    row = pd.Series({"ret_5": 0.03, "rsi_14": 65.0, "macd_hist": np.nan, "vol_21": 0.25})
    ctx = technical_context("AAPL", row, last_close=212.5)
    assert "Ticker: AAPL" in ctx
    assert "Last close: 212.50" in ctx
    assert "ret_5 = +0.0300" in ctx
    assert "macd_hist" not in ctx  # NaN dropped


def test_fundamentals_context_shows_period_over_period():
    facts = pd.DataFrame(
        {
            "metric": ["revenue", "revenue"],
            "period_end": [pd.Timestamp("2025-09-30"), pd.Timestamp("2025-12-31")],
            "value": [100.0, 120.0],
        }
    )
    ctx = fundamentals_context("AAPL", facts)
    assert "revenue" in ctx
    assert "+20.0%" in ctx  # 100 -> 120


def test_fundamentals_context_empty():
    assert "no fundamental data" in fundamentals_context("AAPL", pd.DataFrame())


def test_news_context_lists_headlines():
    scored = pd.DataFrame(
        {
            "title": ["Big product launch"],
            "score": [0.5],
            "confidence": [0.8],
            "event_type": ["product"],
            "published_at": [pd.Timestamp("2026-06-10")],
        }
    )
    ctx = news_context("AAPL", scored)
    assert "Big product launch" in ctx
    assert "score +0.50" in ctx


def test_news_context_empty():
    assert "no recent scored news" in news_context("AAPL", pd.DataFrame())
