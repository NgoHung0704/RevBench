from datetime import date

import pandas as pd

from data_pipeline.quality import check_price_frame


def frame_for(dates: pd.DatetimeIndex, adj_close: list[float]) -> pd.DataFrame:
    n = len(dates)
    assert len(adj_close) == n
    return pd.DataFrame(
        {
            "open": adj_close,
            "high": [p * 1.01 for p in adj_close],
            "low": [p * 0.99 for p in adj_close],
            "close": adj_close,
            "adj_close": adj_close,
            "volume": [1_000_000] * n,
        },
        index=dates,
    )


def test_clean_frame_has_no_issues():
    dates = pd.bdate_range("2026-01-05", periods=20)
    prices = [100 + i * 0.5 for i in range(20)]
    assert check_price_frame(frame_for(dates, prices), "AAPL") == []


def test_single_missing_day_is_treated_as_holiday():
    dates = pd.bdate_range("2026-01-05", periods=20)
    dates = dates.delete(7)  # one missing business day = holiday, not a gap
    prices = [100.0] * len(dates)
    assert check_price_frame(frame_for(dates, prices), "AAPL") == []


def test_gap_detected():
    dates = pd.bdate_range("2026-01-05", periods=30)
    dates = dates.delete([10, 11, 12, 13])  # 4 consecutive missing business days
    prices = [100.0] * len(dates)
    issues = check_price_frame(frame_for(dates, prices), "AAPL")
    assert any("consecutive business days missing" in i for i in issues)


def test_extreme_move_detected():
    dates = pd.bdate_range("2026-01-05", periods=10)
    prices = [100.0] * 5 + [160.0] * 5  # +60% jump → unadjusted split suspicion
    issues = check_price_frame(frame_for(dates, prices), "AAPL")
    assert any("daily move" in i for i in issues)


def test_stale_detected_only_with_as_of():
    dates = pd.bdate_range("2026-01-05", periods=10)
    df = frame_for(dates, [100.0] * 10)
    assert check_price_frame(df, "AAPL") == []
    issues = check_price_frame(df, "AAPL", as_of=date(2026, 3, 1))
    assert any("stale" in i for i in issues)


def test_empty_frame_reported():
    assert check_price_frame(pd.DataFrame(), "AAPL") == ["AAPL: no data"]
