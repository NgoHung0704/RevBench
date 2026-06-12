from datetime import datetime

import numpy as np
import pytest

from agents.config import AgentSettings
from agents.guard import BudgetExceededError, CostGuard
from agents.llm import CallUsage, LLMClient, SchemaValidationError, compute_cost
from agents.roster.sentiment import build_user_message, score_unscored_news
from agents.schemas import SentimentOutput
from agents.store import AgentStore
from agents.testing import NEUTRAL_SENTIMENT, FakeTransport
from data_pipeline.news.base import NewsItem, item_id
from data_pipeline.store import NewsStore

SETTINGS = AgentSettings(deepseek_api_key="test", _env_file=None)

VALID = '{"score": 0.5, "confidence": 0.8, "event_type": "earnings", "summary": "Beat."}'
INVALID_RANGE = '{"score": 7, "confidence": 0.8, "event_type": "earnings", "summary": "x"}'
NOT_JSON = "sorry, here is my analysis instead"


def make_news(ticker: str, n: int) -> list[NewsItem]:
    now = datetime(2026, 6, 10, 12, 0)
    return [
        NewsItem(
            id=item_id(f"https://example.com/{ticker}/{i}"),
            ticker=ticker,
            title=f"Headline {i} about {ticker}",
            summary="Some summary",
            url=f"https://example.com/{ticker}/{i}",
            source="test",
            published_at=now,
            available_at=now,
        )
        for i in range(n)
    ]


def test_compute_cost_flash_known_value():
    # 1M uncached input + 1M output on flash = 0.14 + 0.28
    assert np.isclose(compute_cost("deepseek-v4-flash", 1_000_000, 1_000_000), 0.42)


def test_compute_cost_cache_hits_are_cheap():
    full = compute_cost("deepseek-v4-pro", 100_000, 0, cached_tokens=0)
    cached = compute_cost("deepseek-v4-pro", 100_000, 0, cached_tokens=100_000)
    assert cached < full / 50


def test_complete_json_happy_path():
    client = LLMClient(settings=SETTINGS, transport=FakeTransport([VALID]))
    out = client.complete_json(
        model="deepseek-v4-flash", system="s", user="u", schema=SentimentOutput
    )
    assert out.score == 0.5 and out.event_type == "earnings"


def test_complete_json_retries_once_then_succeeds():
    usages: list[CallUsage] = []
    transport = FakeTransport([INVALID_RANGE, VALID])
    client = LLMClient(settings=SETTINGS, transport=transport, on_usage=usages.append)
    out = client.complete_json(
        model="deepseek-v4-flash", system="s", user="u", schema=SentimentOutput
    )
    assert out.score == 0.5
    assert len(transport.calls) == 2
    assert len(usages) == 2  # the failed attempt cost money too


def test_complete_json_gives_up_after_two_failures():
    transport = FakeTransport([NOT_JSON, INVALID_RANGE])
    client = LLMClient(settings=SETTINGS, transport=transport)
    with pytest.raises(SchemaValidationError):
        client.complete_json(
            model="deepseek-v4-flash", system="s", user="u", schema=SentimentOutput
        )
    assert len(transport.calls) == 2  # exactly one retry, never a loop


def test_cost_guard_blocks_over_budget(tmp_path):
    with AgentStore(tmp_path / "t.duckdb") as store:
        store.record_usage(
            "sentiment",
            CallUsage("deepseek-v4-flash", 1000, 100, 0, cost_usd=2.0),
        )
        guard = CostGuard(store, budget_usd=1.0)
        with pytest.raises(BudgetExceededError):
            guard.check()


def test_score_unscored_news_end_to_end(tmp_path):
    db = tmp_path / "t.duckdb"
    with NewsStore(db) as news_store:
        news_store.upsert(make_news("AAPL", 3))

    with AgentStore(db) as store:
        client = LLMClient(settings=SETTINGS, transport=FakeTransport([NEUTRAL_SENTIMENT]))
        guard = CostGuard(store, budget_usd=1.0)

        run = score_unscored_news(client, store, guard)
        assert run.scored == 3 and run.skipped == 0

        # idempotent: everything is scored now
        rerun = score_unscored_news(client, store, guard)
        assert rerun.scored == 0
        assert len(store.unscored_news()) == 0


def test_dry_run_persists_nothing(tmp_path):
    db = tmp_path / "t.duckdb"
    with NewsStore(db) as news_store:
        news_store.upsert(make_news("MSFT", 2))
    with AgentStore(db) as store:
        client = LLMClient(settings=SETTINGS, transport=FakeTransport())
        run = score_unscored_news(client, store, CostGuard(store, 1.0), persist=False)
        assert run.scored == 2
        assert len(store.unscored_news()) == 2  # still unscored — nothing written


def test_budget_stops_mid_run(tmp_path):
    db = tmp_path / "t.duckdb"
    with NewsStore(db) as news_store:
        news_store.upsert(make_news("NVDA", 5))
    with AgentStore(db) as store:
        # every recorded call instantly exceeds the tiny budget
        client = LLMClient(
            settings=SETTINGS,
            transport=FakeTransport(),
            on_usage=lambda u: store.record_usage(
                "sentiment", CallUsage(u.model, u.prompt_tokens, u.completion_tokens, 0, 99.0)
            ),
        )
        run = score_unscored_news(client, store, CostGuard(store, budget_usd=1.0))
        assert run.stopped_by_budget
        assert run.scored == 1  # first call passes the check, second is blocked


def test_user_message_truncates_long_summaries():
    msg = build_user_message("AAPL", "Title", "x" * 99_999)
    assert len(msg) < 2000
