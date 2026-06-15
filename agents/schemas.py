"""Structured outputs for every agent (CLAUDE.md hard rule #2).

The model never echoes identifiers (ticker, news id) — the caller attaches
them. Pydantic bounds double as guardrails: an out-of-range score fails
validation and triggers the single retry instead of polluting the store.
"""

from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "earnings", "guidance", "mna", "legal", "product",
    "management", "analyst", "macro", "other",
]


class SentimentOutput(BaseModel):
    score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    event_type: EventType
    summary: str = Field(max_length=300)


# --- reasoning agents (deepseek-v4-pro) ---
# Every reasoning agent emits `signal` (-1..1, bearish..bullish over the 5-day
# horizon) + `confidence` so the orchestrator can store a uniform row and the
# fusion layer can treat each agent as one feature.


class TechnicalOutput(BaseModel):
    regime: Literal["uptrend", "downtrend", "range", "volatile"]
    signal: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=500)


class FundamentalsOutput(BaseModel):
    valuation_view: Literal["cheap", "fair", "expensive", "unclear"]
    growth_view: Literal["accelerating", "steady", "decelerating", "unclear"]
    signal: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    red_flags: list[str] = Field(default_factory=list, max_length=5)
    rationale: str = Field(max_length=500)


class NewsOutput(BaseModel):
    key_events: list[str] = Field(default_factory=list, max_length=5)
    catalysts: list[str] = Field(default_factory=list, max_length=5)
    signal: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(max_length=500)


# --- advisory agents (run AFTER fusion, enrich the recommendation) ---


class RiskOutput(BaseModel):
    risk_level: Literal["low", "moderate", "high"]
    max_position_pct: float = Field(ge=0, le=100)  # suggested cap, % of portfolio
    stop_loss_pct: float | None = Field(default=None, ge=0, le=50)
    risk_flags: list[str] = Field(default_factory=list, max_length=5)
    rationale: str = Field(max_length=500)


class StrategistOutput(BaseModel):
    thesis: str = Field(max_length=800)  # prose for the end user
    counterarguments: list[str] = Field(default_factory=list, max_length=4)
    conviction: Literal["low", "medium", "high"]
