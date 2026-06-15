from datetime import datetime

import pandas as pd
import pytest

from data_pipeline.altdata.trends import GoogleTrendsProvider
from data_pipeline.altdata.wikipedia import WikipediaProvider
from data_pipeline.store import AltDataStore
from ml.features.altdata import _point_in_time_align, attention_feature, attention_on_index


def mock_interest_df() -> pd.DataFrame:
    idx = pd.DatetimeIndex(["2025-01-05", "2025-01-12", "2025-01-19"])
    return pd.DataFrame(
        {"iPhone": [40, 55, 80], "isPartial": [False, False, True]}, index=idx
    )


def test_to_points_parses_and_skips_partial():
    points = GoogleTrendsProvider._to_points(mock_interest_df(), "AAPL", "iPhone")
    assert len(points) == 2  # the isPartial current week is dropped
    p = points[0]
    assert p.ticker == "AAPL" and p.value == 40.0 and p.source == "google_trends"
    # available 2 days after the week-end (reporting lag) -> no lookahead
    assert p.available_at == datetime(2025, 1, 7)


def test_to_points_empty_and_missing_keyword():
    assert GoogleTrendsProvider._to_points(pd.DataFrame(), "AAPL", "iPhone") == []
    assert GoogleTrendsProvider._to_points(mock_interest_df(), "AAPL", "Nope") == []


def test_unknown_ticker_rejected():
    with pytest.raises(ValueError, match="no Trends keyword"):
        GoogleTrendsProvider().fetch_series("ZZZZ", None, None)


def test_wikipedia_to_points():
    items = [
        {"timestamp": "2025010100", "views": 12000},
        {"timestamp": "2025010200", "views": 15000},
        {"timestamp": "bad", "views": 1},  # malformed -> skipped
    ]
    points = WikipediaProvider._to_points(items, "AAPL")
    assert len(points) == 2
    assert points[0].source == "wikipedia" and points[0].value == 12000.0
    assert points[0].date == datetime(2025, 1, 1).date()
    assert points[0].available_at == datetime(2025, 1, 2)  # D+1, no lookahead


@pytest.mark.integration
def test_wikipedia_live_fetch():
    from datetime import date

    points = WikipediaProvider().fetch_series("AAPL", date(2025, 1, 1), date(2025, 1, 31))
    assert len(points) > 20 and all(p.value > 0 for p in points)


def test_store_roundtrip_and_dedup(tmp_path):
    points = GoogleTrendsProvider._to_points(mock_interest_df(), "AAPL", "iPhone")
    with AltDataStore(tmp_path / "t.duckdb") as store:
        assert store.upsert(points) == 2
        store.upsert(points)  # idempotent on (source, ticker, date)
        out = store.load("google_trends", "AAPL")
        assert len(out) == 2
        assert list(out["value"]) == [40.0, 55.0]


def test_attention_feature_is_relative_to_trailing_median():
    # constant 50 then a jump to 100 -> ASVI ~ +1.0 (double the median)
    dates = pd.bdate_range("2025-01-06", periods=10)
    rows = [
        {"ticker": "AAPL", "date": d, "value": v,
         "available_at": d + pd.Timedelta(days=2)}
        for d, v in zip(dates, [50] * 9 + [100], strict=True)
    ]
    feat = attention_feature(pd.DataFrame(rows), window=4)
    assert feat["AAPL"].iloc[-1] > 0.9  # 100 vs median ~50


def test_attention_on_index_point_in_time():
    # one ticker, daily values; feature available the day after each value
    dates = pd.bdate_range("2025-01-06", periods=12)
    rows = [
        {"ticker": "AAPL", "date": d, "value": v,
         "available_at": d + pd.Timedelta(days=1)}
        for d, v in zip(dates, [50] * 6 + [100] * 6, strict=True)
    ]
    idx = pd.MultiIndex.from_arrays(
        [pd.bdate_range("2025-01-06", periods=12), ["AAPL"] * 12], names=["date", "ticker"]
    )
    s = attention_on_index(pd.DataFrame(rows), idx, window=4)
    # the value for day d (published d+1) cannot appear on day d itself
    by_date = s.droplevel("ticker")
    assert by_date.loc["2025-01-06"] != by_date.loc["2025-01-06"]  # NaN early (no median yet)
    # a ticker not in the altdata gets all-NaN, no crash
    idx2 = pd.MultiIndex.from_arrays(
        [pd.bdate_range("2025-01-06", periods=3), ["ZZZZ"] * 3], names=["date", "ticker"]
    )
    assert attention_on_index(pd.DataFrame(rows), idx2).isna().all()


def test_point_in_time_align_no_lookahead():
    feature = pd.Series([0.5], index=pd.DatetimeIndex(["2025-01-07"]))  # available Jan 7
    forward = pd.Series(
        [0.01, 0.02], index=pd.DatetimeIndex(["2025-01-06", "2025-01-09"])
    )
    aligned = _point_in_time_align(feature, forward)
    # Jan 6 is before the feature is available -> excluded; Jan 9 sees it
    assert list(aligned.index) == [pd.Timestamp("2025-01-09")]
    assert aligned.iloc[0]["f"] == 0.5
