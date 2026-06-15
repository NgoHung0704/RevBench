import pandas as pd

from ml.features.sentiment import daily_sentiment

IDX = pd.date_range("2026-06-01", "2026-06-20", freq="D")  # fixed grid for assertions


def _scored(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["ticker", "published_at", "score", "confidence"])


def test_feature_excludes_same_day_article_no_leak():
    """The feature at date t must not include an article published on day t —
    that would be lookahead. shift(1) enforces it."""
    scored = _scored([("AAPL", "2026-06-10", 1.0, 1.0)])
    feat = daily_sentiment(scored, window_days=5, index=IDX)
    assert pd.isna(feat.loc["2026-06-10", "AAPL"])  # same day excluded
    assert feat.loc["2026-06-11", "AAPL"] == 1.0  # next day sees it


def test_confidence_weighted_mean():
    scored = _scored([
        ("AAPL", "2026-06-10", 1.0, 0.9),
        ("AAPL", "2026-06-10", -1.0, 0.1),
    ])
    feat = daily_sentiment(scored, window_days=5, index=IDX)
    val = feat.loc["2026-06-11", "AAPL"]
    assert val == (1.0 * 0.9 - 1.0 * 0.1) / (0.9 + 0.1)  # 0.8


def test_window_decay():
    scored = _scored([("AAPL", "2026-06-01", 1.0, 1.0)])
    feat = daily_sentiment(scored, window_days=3, index=IDX)
    # within 3 days after publication it still contributes, then drops out
    assert feat.loc["2026-06-02", "AAPL"] == 1.0
    assert pd.isna(feat.loc["2026-06-10", "AAPL"])


def test_empty_input():
    assert daily_sentiment(pd.DataFrame()).empty


def test_multiple_tickers_independent():
    scored = _scored([
        ("AAPL", "2026-06-10", 1.0, 1.0),
        ("MSFT", "2026-06-10", -1.0, 1.0),
    ])
    feat = daily_sentiment(scored, window_days=5, index=IDX)
    assert feat.loc["2026-06-11", "AAPL"] == 1.0
    assert feat.loc["2026-06-11", "MSFT"] == -1.0
