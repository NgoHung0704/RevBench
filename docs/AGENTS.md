# RevBench — Agent System Design

> LLM: **DeepSeek V4** via the OpenAI-compatible API (see [DECISIONS.md](DECISIONS.md) D3, re-decided 2026-06-12). Per D4 we call the SDK directly (`openai` + `base_url`), no middleware framework. Each agent's model ID is **config**, not hard-coded — upgrading/switching a single agent's provider is a one-line change.

## Philosophy

- **An agent is an analyst, not a calculator.** The numbers (RSI, P/E, returns) are computed by code beforehand and fed into the prompt. The agent reads, reasons, and connects information — what an LLM is actually good at.
- **Every output is structured JSON**: JSON mode + Pydantic validation (one corrective retry on a parse failure) → stored in the DB, backtestable.
- **The reasoning trail is stored** and displayed in the UI — explainability is the product's main selling point.
- **Cost is a first-class design constraint**: a daily ceiling in code (`AGENT_DAILY_BUDGET_USD=1`), exceeding it stops the run + alerts. Jobs run inside the **off-peak window (16:30–00:30 UTC, −50%)** — the existing 22:30 Paris schedule already falls inside it.

## Roster

| Agent | Model | When it runs | Input | Output (schema) |
|---|---|---|---|---|
| **Sentiment** | `deepseek-v4-flash` | Nightly, every new article | One news item (from DB) | `{ticker, score: -1..1, confidence, event_type, summary_1line}` |
| **News** | `deepseek-v4-pro` | Daily/ticker | Top scored news from the DB (RSS + GDELT) | `{key_events[], materiality, catalysts[], citations[]}` |
| **Technical** | `deepseek-v4-pro` | Daily/ticker | The indicator table computed by `ml/features` | `{regime, sr_levels[], signal: -1..1, rationale}` |
| **Fundamentals** | `deepseek-v4-pro` | After each earnings + weekly | Quarterly figures from the DB (EDGAR) | `{valuation_view, growth_view, red_flags[], signal: -1..1}` |
| **AltData** | `deepseek-v4-pro` | Weekly | Trends/Reddit/pageviews series | `{demand_signal, attention_anomaly, signal: -1..1}` |
| **Risk** | `deepseek-v4-pro` | Daily/ticker | Vol, drawdown, earnings calendar, proposed position | `{risk_flags[], max_position_pct, stop_suggestion}` |
| **Strategist** | `deepseek-v4-pro` | Daily/ticker, runs last | All signals + the fusion output | `{action, confidence, horizon_days, thesis_for_user, counterarguments[]}` |

**Orchestrator** (plain code, not an LLM): runs the DAG above — fan out News/Technical/Fundamentals/AltData in parallel → Risk → Strategist; gather the results, write to the DB, track cost.

**Note vs the old Claude design:** no server-side web search — the News Agent works entirely off the internal news store (Phase 1 already handles collection). This is the trade-off accepted in D3.

## Key code patterns

```python
# agents/llm.py — shared client (sketch)
from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

# agents/roster/sentiment.py — sketch
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    max_tokens=400,
    temperature=0,                            # deterministic -> reproducible backtests
    response_format={"type": "json_object"},  # JSON mode
    messages=[
        # FROZEN system prompt (no timestamps) -> ~99% cheaper input on prefix-cache hits
        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": article_text},
    ],
)
result = SentimentOutput.model_validate_json(response.choices[0].message.content)
usage = response.usage  # prompt_tokens (+ cached), completion_tokens → cost guard
```

## Cost control (mandatory, not optional)

1. **Frozen system prompt** — no timestamps/IDs embedded (breaks the prefix cache). Dynamic context goes in the user message.
2. **Run inside the off-peak window** (16:30–00:30 UTC, −50%) — the current 22:30 Paris schedule already satisfies this.
3. **Cost guard** in the orchestrator: read `response.usage` on every call (cached tokens are priced separately), accumulate the daily total in the DB, exceed `AGENT_DAILY_BUDGET_USD` → stop + log.
4. **JSON parse failure → retry exactly once**, then skip that record (logged) — never loop forever.
5. During dev: run 2–3 tickers instead of the whole universe.

## Agent evaluation (Phase 4.5)

- Every agent `signal: -1..1` is stored with history → compute the **Information Coefficient** (correlation of the signal with forward returns) like any other ML feature.
- Ablation: fusion with/without each agent → a "which agent earns its keep" table.
- Sentiment Agent: evaluated separately against a ~200-article hand-labeled set (precision/recall by event_type).
- **Model A/B (done 2026-06-13, `python -m agents.compare`):** Flash vs Pro on sentiment — close agreement (mean |Δscore| ≈ 0.10), Pro *more compressed* on strong headlines and 8× pricier → **Flash kept**, with `temperature=0` for reproducibility. Re-run when adding a harder agent to decide if Pro is worth it there.
