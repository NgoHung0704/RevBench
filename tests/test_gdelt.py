from datetime import datetime

import pytest

from data_pipeline.news.base import ProviderRateLimited
from data_pipeline.news.gdelt import GDELTProvider

ARTICLES = [
    {
        "url": "https://example.com/nvda-1",
        "title": "NVIDIA earnings beat expectations",
        "seendate": "20260611T143000Z",
    },
    {"title": "no url, must be skipped", "seendate": "20260611T150000Z"},
    {"url": "https://example.com/nvda-2", "title": "bad date", "seendate": "not-a-date"},
]


def test_to_items_parses_and_skips_unusable():
    items = GDELTProvider._to_items(ARTICLES, "NVDA")
    assert len(items) == 1  # missing url and unparseable seendate both skipped
    item = items[0]
    assert item.ticker == "NVDA"
    assert item.source == "gdelt"
    assert item.published_at == datetime(2026, 6, 11, 14, 30, 0)
    assert item.available_at == item.published_at


def test_unknown_ticker_rejected():
    with pytest.raises(ValueError, match="not in the universe"):
        GDELTProvider().fetch_for_ticker("ZZZZ")


def test_429_fails_fast_without_retry(monkeypatch):
    class Fake429:
        status_code = 429

    calls: list[int] = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return Fake429()

    monkeypatch.setattr("data_pipeline.news.gdelt.requests.get", fake_get)
    with pytest.raises(ProviderRateLimited):
        GDELTProvider().fetch_for_ticker("AAPL")
    assert len(calls) == 1  # retrying against an IP cooldown would only extend it


@pytest.mark.integration
def test_real_gdelt_nvda():
    items = GDELTProvider().fetch_for_ticker("NVDA")
    assert all(i.ticker == "NVDA" and i.url for i in items)
