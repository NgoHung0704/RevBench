import pandas as pd
import pytest

from data_pipeline.fundamentals.edgar import EdgarClient, normalize_facts
from data_pipeline.store import FundamentalsStore

RAW = {
    "facts": {
        "us-gaap": {
            # first revenue candidate tag absent -> falls back to "Revenues"
            "Revenues": {
                "units": {
                    "USD": [
                        {
                            "start": "2025-10-01", "end": "2025-12-31", "val": 1000,
                            "accn": "acc-1", "fy": 2026, "fp": "Q1",
                            "form": "10-Q", "filed": "2026-02-01",
                        },
                        {
                            "start": "2025-01-01", "end": "2025-12-31", "val": 4000,
                            "accn": "acc-2", "fy": 2025, "fp": "FY",
                            "form": "10-K", "filed": "2026-02-15",
                        },
                        {  # 8-K must be excluded
                            "end": "2025-12-31", "val": 999,
                            "accn": "acc-3", "form": "8-K", "filed": "2026-01-20",
                        },
                        {  # exact duplicate of acc-1 (appears in several XBRL frames)
                            "start": "2025-10-01", "end": "2025-12-31", "val": 1000,
                            "accn": "acc-1", "fy": 2026, "fp": "Q1",
                            "form": "10-Q", "filed": "2026-02-01",
                        },
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "start": "2025-10-01", "end": "2025-12-31", "val": 250,
                            "accn": "acc-1", "fy": 2026, "fp": "Q1",
                            "form": "10-Q", "filed": "2026-02-01",
                        }
                    ]
                }
            },
            "EarningsPerShareDiluted": {
                "units": {
                    "USD/shares": [
                        {
                            "start": "2025-10-01", "end": "2025-12-31", "val": 1.61,
                            "accn": "acc-1", "fy": 2026, "fp": "Q1",
                            "form": "10-Q", "filed": "2026-02-01",
                        }
                    ]
                }
            },
        }
    }
}


def test_normalize_extracts_metrics_and_filters_forms():
    df = normalize_facts(RAW, "AAPL")
    assert set(df["metric"]) == {"revenue", "net_income", "eps_diluted"}
    assert len(df[df["metric"] == "revenue"]) == 2  # 8-K excluded, duplicate collapsed
    assert (df["ticker"] == "AAPL").all()


def test_normalize_available_at_is_next_day():
    df = normalize_facts(RAW, "AAPL")
    q1 = df[(df["metric"] == "revenue") & (df["accn"] == "acc-1")].iloc[0]
    assert q1["filed"] == pd.Timestamp("2026-02-01")
    assert q1["available_at"] == pd.Timestamp("2026-02-02")  # filed + 1 day, conservative


def test_normalize_empty_facts():
    assert normalize_facts({"facts": {}}, "AAPL").empty


def test_fundamentals_store_roundtrip_idempotent(tmp_path):
    df = normalize_facts(RAW, "AAPL")
    with FundamentalsStore(tmp_path / "t.duckdb") as store:
        n1 = store.upsert(df)
        store.upsert(df)  # re-ingest must not duplicate
        out = store.load("AAPL")
        assert len(out) == n1 == 4
        rev = store.load("AAPL", metric="revenue")
        assert list(rev["value"]) == [1000.0, 4000.0]


@pytest.mark.integration
def test_real_edgar_aapl():
    df = EdgarClient().quarterly_facts("AAPL")
    assert not df.empty
    assert {"revenue", "net_income", "eps_diluted"} <= set(df["metric"])
    assert (df["available_at"] > df["filed"]).all()
