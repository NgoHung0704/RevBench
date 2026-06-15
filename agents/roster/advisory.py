"""Advisory agents (deepseek-v4-pro): Risk + Strategist.

They run AFTER fusion and enrich the recommendation — Risk sizes the position
and flags hazards, Strategist turns everything into an honest user-facing thesis.
Same thin-call shape as the reasoning agents (temperature=0, room for the
thinking model's reasoning trace).
"""

from ..llm import LLMClient
from ..prompts.risk import RISK_SYSTEM
from ..prompts.strategist import STRATEGIST_SYSTEM
from ..schemas import RiskOutput, StrategistOutput

ADVISORY_TEMPERATURE = 0.0
ADVISORY_MAX_TOKENS = 4000


def analyze_risk(client: LLMClient, context: str) -> RiskOutput:
    return client.complete_json(
        model=client.settings.reasoning_model,
        system=RISK_SYSTEM,
        user=context,
        schema=RiskOutput,
        max_tokens=ADVISORY_MAX_TOKENS,
        temperature=ADVISORY_TEMPERATURE,
    )


def analyze_strategy(client: LLMClient, context: str) -> StrategistOutput:
    return client.complete_json(
        model=client.settings.reasoning_model,
        system=STRATEGIST_SYSTEM,
        user=context,
        schema=StrategistOutput,
        max_tokens=ADVISORY_MAX_TOKENS,
        temperature=ADVISORY_TEMPERATURE,
    )
