"""OpenAI-shaped fake transport for tests and --dry-run (no key, no cost)."""

from itertools import cycle
from types import SimpleNamespace

NEUTRAL_SENTIMENT = (
    '{"score": 0.0, "confidence": 0.2, "event_type": "other",'
    ' "summary": "Canned dry-run response."}'
)
NEUTRAL_NEWS = (
    '{"key_events": [], "catalysts": [], "signal": 0.0, "confidence": 0.2,'
    ' "summary": "Canned dry-run news synthesis."}'
)
NEUTRAL_TECHNICAL = (
    '{"regime": "range", "signal": 0.0, "confidence": 0.3,'
    ' "rationale": "Canned dry-run technical read."}'
)
NEUTRAL_FUNDAMENTALS = (
    '{"valuation_view": "unclear", "growth_view": "unclear", "signal": 0.0,'
    ' "confidence": 0.2, "red_flags": [], "rationale": "Canned dry-run."}'
)
# orchestrator call order per ticker: news -> technical -> fundamentals
REASONING_CYCLE = [NEUTRAL_NEWS, NEUTRAL_TECHNICAL, NEUTRAL_FUNDAMENTALS]


class FakeTransport:
    """Mimics `client.chat.completions.create`; replays canned payloads."""

    def __init__(self, payloads: list[str] | None = None):
        self._payloads = cycle(payloads or [NEUTRAL_SENTIMENT])
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=next(self._payloads)))],
            usage=SimpleNamespace(
                prompt_tokens=200, completion_tokens=50, prompt_cache_hit_tokens=120
            ),
        )
