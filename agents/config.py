"""Agent configuration (docs/DECISIONS.md D3 — DeepSeek V4, D4 — direct SDK).

Per-agent model IDs are config, not code: upgrading one agent (or switching
provider entirely) is a one-line change here, nothing else moves.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    agent_daily_budget_usd: float = 1.0

    reasoning_model: str = "deepseek-v4-pro"
    sentiment_model: str = "deepseek-v4-flash"


# USD per 1M tokens, verified 2026-06-12 (docs/DECISIONS.md D3).
PRICING: dict[str, dict[str, float]] = {
    "deepseek-v4-pro": {"input": 0.435, "cached_input": 0.004, "output": 0.87},
    "deepseek-v4-flash": {"input": 0.14, "cached_input": 0.0028, "output": 0.28},
}
