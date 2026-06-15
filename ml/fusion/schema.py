"""Recommendation schema + fusion config (docs/PLAN.md 4.1).

The recommendation is the product's final, user-facing output. It is NOT advice
(disclaimer everywhere) and it is fully deterministic: the same inputs always
produce the same recommendation, so it can be stored, audited, and backtested.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

Action = Literal["buy", "hold", "sell"]


@dataclass(frozen=True)
class FusionConfig:
    """Hand-set weights — PLAN 4.2 wants these learned from the backtest, which
    needs accumulated agent-signal history (docs/REVISIT.md R6). Defaults until
    then: the ML leg and the agent consensus get equal say; agents are weighted
    by their own confidence."""

    ml_weight: float = 0.5
    agent_weight: float = 0.5
    buy_threshold: float = 0.15
    sell_threshold: float = -0.15


@dataclass
class Recommendation:
    ticker: str
    as_of_date: date
    action: Action
    score: float  # combined signal in [-1, 1]
    confidence: float  # [0, 1]
    ml_proba: float | None  # model P(up) in [0, 1], None if no model
    components: dict[str, float] = field(default_factory=dict)  # per-leg signal
    rationale: str = ""
