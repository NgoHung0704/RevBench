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


def test_fundamentals_context_uses_clean_quarterly_yoy():
    rows = []
    for pe, val in [("2024-03-31", 100), ("2024-06-30", 110), ("2024-09-30", 120),
                    ("2024-12-31", 130), ("2025-03-31", 125)]:
        e = pd.Timestamp(pe)
        rows.append({"metric": "revenue", "period_start": e - pd.Timedelta(days=90),
                     "period_end": e, "value": float(val), "filed": e + pd.Timedelta(days=20)})
    # an annual 10-K value that, compared naively, would look like a huge spike
    rows.append({"metric": "revenue", "period_start": pd.Timestamp("2024-01-01"),
                 "period_end": pd.Timestamp("2024-12-31"), "value": 460.0,
                 "filed": pd.Timestamp("2025-01-20")})
    ctx = fundamentals_context("AAPL", pd.DataFrame(rows))
    assert "quarterly" in ctx
    assert "460" not in ctx  # annual value excluded -> no fake spike
    assert "YoY +25.0%" in ctx  # 125 vs 100 four quarters earlier  # 100 -> 120


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
