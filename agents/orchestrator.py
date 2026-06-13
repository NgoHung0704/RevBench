"""Phase 3 orchestrator: per-ticker fan-out of the reasoning agents.

For each ticker, as of the latest available date, it builds point-in-time
context from the DB and runs News / Technical / Fundamentals, storing one
agent_signals row per (ticker, date, agent). Plain code, no LLM — the DAG is a
simple fan-out (Risk/Strategist join in Phase 4).

Cost: every call's usage lands in the agent_usage ledger; the budget guard is
checked before each call and stops the whole run when the ceiling is hit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from data_pipeline.store import DEFAULT_DB_PATH, FundamentalsStore
from data_pipeline.universe import TICKERS
from ml.data import load_frames
from ml.features.technical import WARMUP_DAYS, compute_features

from .config import AgentSettings
from .context import fundamentals_context, news_context, technical_context
from .guard import BudgetExceededError, CostGuard
from .llm import CallUsage, LLMClient, SchemaValidationError
from .roster.reasoning import analyze_fundamentals, analyze_news, analyze_technical
from .store import AgentStore

logger = logging.getLogger("revbench.agents.orchestrator")


class _UsageTracker:
    """Attributes each LLM call's cost to the agent currently running."""

    def __init__(self, store: AgentStore):
        self.store = store
        self.agent = "orchestrator"
        self.total = 0.0

    def __call__(self, usage: CallUsage) -> None:
        self.store.record_usage(self.agent, usage)
        self.total += usage.cost_usd


@dataclass
class TickerResult:
    ticker: str
    signals: dict[str, float] = field(default_factory=dict)
    failed: list[str] = field(default_factory=list)


@dataclass
class OrchestratorRun:
    as_of_date: object = None
    results: list[TickerResult] = field(default_factory=list)
    stopped_by_budget: bool = False
    cost_usd: float = 0.0


def _build_contexts(
    ticker: str, frames: dict, fundamentals: FundamentalsStore,
    agent_store: AgentStore, as_of_ts: pd.Timestamp,
) -> dict[str, str]:
    """Point-in-time context per agent (only data knowable at as_of)."""
    df = frames[ticker]
    feats = compute_features(df)
    last = feats.dropna().iloc[-1]
    last_close = float(df["adj_close"].iloc[-1])

    facts = fundamentals.load(ticker)
    if not facts.empty:
        facts = facts[pd.to_datetime(facts["available_at"]) <= as_of_ts]

    return {
        "news": news_context(ticker, agent_store.scored_news_for(ticker)),
        "technical": technical_context(ticker, last, last_close),
        "fundamentals": fundamentals_context(ticker, facts),
    }


def run_ticker(
    client: LLMClient, agent_store: AgentStore, guard: CostGuard,
    tracker: _UsageTracker, ticker: str, contexts: dict[str, str],
    as_of_date, persist: bool,
) -> TickerResult | None:
    """Run the three reasoning agents for one ticker. None => stopped by budget."""
    result = TickerResult(ticker)
    agents = [
        ("news", analyze_news),
        ("technical", analyze_technical),
        ("fundamentals", analyze_fundamentals),
    ]
    for name, analyze in agents:
        try:
            guard.check()
        except BudgetExceededError as exc:
            logger.warning("stopping: %s", exc)
            return None
        tracker.agent = name
        try:
            out = analyze(client, contexts[name])
        except SchemaValidationError as exc:
            logger.warning("%s/%s failed: %s", ticker, name, exc)
            result.failed.append(name)
            continue
        result.signals[name] = out.signal
        if persist:
            agent_store.upsert_signal(
                ticker=ticker, as_of_date=as_of_date, agent=name,
                signal=out.signal, confidence=out.confidence,
                payload_json=out.model_dump_json(), model=client.settings.reasoning_model,
            )
    return result


def run_signals(
    client: LLMClient,
    agent_store: AgentStore,
    guard: CostGuard,
    tracker: _UsageTracker,
    tickers: tuple[str, ...] = TICKERS,
    db_path=DEFAULT_DB_PATH,
    persist: bool = True,
) -> OrchestratorRun:
    frames = load_frames(db_path, tickers)
    run = OrchestratorRun()
    if not frames:
        logger.warning("no price data — run data_pipeline.fetch first")
        return run

    as_of_ts = max(f.index.max() for f in frames.values())
    run.as_of_date = as_of_ts.date()

    with FundamentalsStore(db_path) as fundamentals:
        for ticker in tickers:
            if ticker not in frames or len(frames[ticker]) <= WARMUP_DAYS:
                logger.info("skip %s: insufficient price history", ticker)
                continue
            contexts = _build_contexts(ticker, frames, fundamentals, agent_store, as_of_ts)
            res = run_ticker(
                client, agent_store, guard, tracker, ticker, contexts, run.as_of_date, persist
            )
            if res is None:
                run.stopped_by_budget = True
                break
            run.results.append(res)

    run.cost_usd = tracker.total
    return run


def build_live_client(settings: AgentSettings, tracker: _UsageTracker) -> LLMClient:
    return LLMClient(settings=settings, on_usage=tracker)
