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
