"""Enrichment pass: Risk + Strategist agents augment the fused recommendations.

Runs after fusion (PLAN 4.3/4.4). For each recommendation it computes risk
statistics from prices (code), asks the Risk Agent to size the position, then
asks the Strategist Agent for an honest user-facing thesis, and writes both
back onto the recommendation row.
"""

from __future__ import annotations

import logging

from ml.data import load_frames

from .context import risk_context, risk_stats, strategist_context
from .guard import BudgetExceededError, CostGuard
from .llm import LLMClient, SchemaValidationError
from .orchestrator import _UsageTracker
from .roster.advisory import analyze_risk, analyze_strategy

logger = logging.getLogger("revbench.agents.advisory")


def enrich_recommendations(
    db_path,
    recs: list,
    client: LLMClient,
    rec_store,
    guard: CostGuard,
    tracker: _UsageTracker,
    frames: dict | None = None,
) -> int:
    """Add Risk + Strategist output to each recommendation. Returns count enriched."""
    if frames is None:
        frames = load_frames(db_path, tuple(r.ticker for r in recs))

    enriched = 0
    for rec in recs:
        frame = frames.get(rec.ticker)
        if frame is None or len(frame) < 30:
            continue
        try:
            guard.check()
        except BudgetExceededError as exc:
            logger.warning("stopping enrichment: %s", exc)
            break

        stats = risk_stats(frame)
        try:
            tracker.agent = "risk"
            risk = analyze_risk(
                client, risk_context(rec.ticker, rec.action, rec.score, stats)
            )
            tracker.agent = "strategist"
            strat = analyze_strategy(
                client,
                strategist_context(
                    rec.ticker, rec.action, rec.score, rec.components,
                    risk.risk_level, risk.risk_flags,
                ),
            )
        except SchemaValidationError as exc:
            logger.warning("enrichment failed for %s: %s", rec.ticker, exc)
            continue

        rec_store.update_advice(rec.ticker, rec.as_of_date, risk, strat)
        enriched += 1
    return enriched
