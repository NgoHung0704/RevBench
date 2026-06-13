"""Reasoning agents (deepseek-v4-pro): Technical, Fundamentals, News.

Each is a thin call: a frozen system prompt + a context string -> a validated,
bounded output. They run at temperature=0 so a given context reproduces the
same signal (point-in-time backtests must be re-runnable). The orchestrator
builds the context and persists the result.
"""

from ..llm import LLMClient
from ..prompts.fundamentals import FUNDAMENTALS_SYSTEM
from ..prompts.news import NEWS_SYSTEM
from ..prompts.technical import TECHNICAL_SYSTEM
from ..schemas import FundamentalsOutput, NewsOutput, TechnicalOutput

REASONING_TEMPERATURE = 0.0
# deepseek-v4-pro is a thinking model: it emits reasoning_content separately and
# the answer only lands in content *after* it finishes thinking. max_tokens caps
# both, so it must leave room for the reasoning trace (often 500–1500 tokens) or
# content comes back empty. We only pay for tokens actually used, so a high
# ceiling is free insurance against truncation. News synthesis is the most
# verbose (many events + catalysts), so size for that.
REASONING_MAX_TOKENS = 4000


def analyze_technical(client: LLMClient, context: str) -> TechnicalOutput:
    return client.complete_json(
        model=client.settings.reasoning_model,
        system=TECHNICAL_SYSTEM,
        user=context,
        schema=TechnicalOutput,
        max_tokens=REASONING_MAX_TOKENS,
        temperature=REASONING_TEMPERATURE,
    )


def analyze_fundamentals(client: LLMClient, context: str) -> FundamentalsOutput:
    return client.complete_json(
        model=client.settings.reasoning_model,
        system=FUNDAMENTALS_SYSTEM,
        user=context,
        schema=FundamentalsOutput,
        max_tokens=REASONING_MAX_TOKENS,
        temperature=REASONING_TEMPERATURE,
    )


def analyze_news(client: LLMClient, context: str) -> NewsOutput:
    return client.complete_json(
        model=client.settings.reasoning_model,
        system=NEWS_SYSTEM,
        user=context,
        schema=NewsOutput,
        max_tokens=REASONING_MAX_TOKENS,
        temperature=REASONING_TEMPERATURE,
    )
