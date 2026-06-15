import pandas as pd

from data_pipeline.fundamentals.normalize import quarterly_series


def _row(period_end, value, days=90, filed=None, metric="revenue"):
    end = pd.Timestamp(period_end)
    return {
        "metric": metric,
        "period_start": end - pd.Timedelta(days=days),
        "period_end": end,
        "value": float(value),
        "filed": pd.Timestamp(filed) if filed else end + pd.Timedelta(days=20),
    }


def test_keeps_quarterly_drops_annual():
    rows = [
        _row("2024-03-31", 100), _row("2024-06-30", 110), _row("2024-09-30", 120),
        _row("2024-12-31", 130), _row("2025-03-31", 125),
        _row("2024-12-31", 460, days=363),  # annual 10-K -> excluded by duration
    ]
    s = quarterly_series(pd.DataFrame(rows))
    assert (s["period_type"] == "quarterly").all()
    assert 460.0 not in set(s["value"])  # the annual spike is gone
    last = s[s["period_end"] == pd.Timestamp("2025-03-31")].iloc[0]
    assert abs(last["yoy"] - 0.25) < 1e-9  # 125 vs 100 four quarters back


def test_annual_fallback_when_no_quarterly():
    rows = [_row("2023-12-31", 400, days=363), _row("2024-12-31", 440, days=363)]
    s = quarterly_series(pd.DataFrame(rows))
    assert (s["period_type"] == "annual").all()
    assert abs(s.iloc[-1]["yoy"] - 0.1) < 1e-9  # 440 vs 400 a year back


def test_restated_duplicate_keeps_latest_filed():
    rows = [
        _row("2024-03-31", 100, filed="2024-04-20"),
        _row("2024-03-31", 105, filed="2025-04-20"),  # restated in a later filing
    ]
    s = quarterly_series(pd.DataFrame(rows))
    assert len(s) == 1
    assert s.iloc[0]["value"] == 105.0


def test_empty():
    assert quarterly_series(pd.DataFrame()).empty
