"""Shared LLM client: JSON mode + Pydantic validation + cost accounting.

DeepSeek V4 over the OpenAI-compatible API (docs/DECISIONS.md D3). Invalid
JSON gets exactly one corrective retry, then the record is skipped — bulk
pipelines must never loop on one bad article. Every attempt's usage (including
failed ones — they cost money too) is reported through `on_usage`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .config import PRICING, AgentSettings

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class CallUsage:
    model: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    cost_usd: float


def compute_cost(
    model: str, prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0
) -> float:
    price = PRICING[model]
    uncached = max(prompt_tokens - cached_tokens, 0)
    return (
        uncached * price["input"]
        + cached_tokens * price["cached_input"]
        + completion_tokens * price["output"]
    ) / 1e6


class SchemaValidationError(ValueError):
    """Model output failed schema validation twice — skip the record."""


class LLMClient:
    def __init__(
        self,
        settings: AgentSettings | None = None,
        transport=None,  # injectable OpenAI-shaped client for tests / dry runs
        on_usage: Callable[[CallUsage], None] | None = None,
    ):
        self.settings = settings or AgentSettings()
        self.on_usage = on_usage
        if transport is not None:
            self._client = transport
        else:
            if not self.settings.deepseek_api_key:
                raise RuntimeError(
                    "DEEPSEEK_API_KEY is not set — copy .env.example to .env and fill it in"
                )
            from openai import OpenAI  # imported lazily so offline tests never need it

            self._client = OpenAI(
                base_url=self.settings.deepseek_base_url,
                api_key=self.settings.deepseek_api_key,
            )

    def complete_json(
        self, *, model: str, system: str, user: str, schema: type[T], max_tokens: int = 1024
    ) -> T:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error: ValidationError | None = None
        for _attempt in range(2):
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            self._report_usage(model, response)
            content = response.choices[0].message.content or ""
            try:
                return schema.model_validate_json(content)
            except ValidationError as exc:
                last_error = exc
                messages = [
                    *messages,
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            f"That JSON failed validation: {exc.error_count()} error(s): "
                            f"{exc.errors()[0]['msg']} at {exc.errors()[0]['loc']}. "
                            "Reply again with ONLY the corrected JSON object."
                        ),
                    },
                ]
        raise SchemaValidationError(f"output failed schema validation twice: {last_error}")

    def _report_usage(self, model: str, response) -> None:
        u = response.usage
        cached = getattr(u, "prompt_cache_hit_tokens", 0) or 0  # DeepSeek-specific field
        usage = CallUsage(
            model=model,
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            cached_tokens=cached,
            cost_usd=compute_cost(model, u.prompt_tokens, u.completion_tokens, cached),
        )
        if self.on_usage is not None:
            self.on_usage(usage)
