from datetime import datetime

import feedparser
import pytest

from data_pipeline.news.base import NewsItem, item_id
from data_pipeline.news.rss import YahooRSSProvider
from data_pipeline.store import NewsStore

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test feed</title>
<item>
  <title>Apple unveils new chip</title>
  <link>https://example.com/a1</link>
  <pubDate>Thu, 11 Jun 2026 14:00:00 GMT</pubDate>
  <description>Summary A</description>
</item>
<item>
  <title>Item without link</title>
  <description>must be skipped</description>
</item>
<item>
  <title>Second article</title>
  <link>https://example.com/a2</link>
  <pubDate>Thu, 11 Jun 2026 15:30:00 GMT</pubDate>
</item>
<item>
  <title>Duplicate of first URL</title>
  <link>https://example.com/a1</link>
  <pubDate>Thu, 11 Jun 2026 16:00:00 GMT</pubDate>
</item>
</channel></rss>"""


def parsed_items() -> list[NewsItem]:
    return YahooRSSProvider._to_items(feedparser.parse(RSS_XML), "AAPL")


def test_to_items_parses_and_skips_linkless():
    items = parsed_items()
    assert len(items) == 3  # linkless entry skipped, duplicate URL kept (store dedups)
    first = items[0]
    assert first.title == "Apple unveils new chip"
    assert first.published_at == datetime(2026, 6, 11, 14, 0, 0)
    assert first.available_at == first.published_at
    assert first.id == item_id("https://example.com/a1")


def test_store_dedups_within_and_across_batches(tmp_path):
    items = parsed_items()
    with NewsStore(tmp_path / "t.duckdb") as store:
        store.upsert(items)
        store.upsert(items)  # second fetch returns the same articles
        out = store.load("AAPL")
        assert len(out) == 2  # a1 (deduped) + a2


def test_same_article_two_tickers_kept(tmp_path):
    items = parsed_items()[:1]
    other = items[0].model_copy(update={"ticker": "MSFT"})
    with NewsStore(tmp_path / "t.duckdb") as store:
        store.upsert(items + [other])
        assert len(store.load()) == 2
        assert len(store.load("MSFT")) == 1


def test_upsert_empty_is_noop(tmp_path):
    with NewsStore(tmp_path / "t.duckdb") as store:
        assert store.upsert([]) == 0


@pytest.mark.integration
def test_real_yahoo_rss_aapl():
    items = YahooRSSProvider().fetch_for_ticker("AAPL")
    assert len(items) > 0
    assert all(i.ticker == "AAPL" and i.url for i in items)
