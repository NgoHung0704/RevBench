# CLAUDE.md — RevBench

AI decision-support system for blue-chip stocks on Revolut. Student research project (INSA Lyon 4IF). **Not financial advice** — every user-facing surface carries a disclaimer.

## Source of truth
- Roadmap & current phase: `docs/PLAN.md` (work proceeds phase by phase — check status there first).
- Open/closed tech decisions: `docs/DECISIONS.md` (`[D#]` references). **Do not re-litigate closed decisions; do not silently decide open ones — propose, then let the user close them.**
- Architecture invariants: `docs/ARCHITECTURE.md`. Agent design: `docs/AGENTS.md`.

## Hard rules
1. **Point-in-time correctness**: every stored record gets an `available_at` timestamp; backtests may only read data with `available_at <= t`. Any PR touching features/backtest must be checked against the bias checklist in `docs/FINANCE_PRIMER.md` §1.3.
2. **Agents interpret, code computes**: LLMs never compute indicators/statistics — `ml/features` does. Agent outputs are structured JSON (Pydantic + `output_config.format`), always persisted.
3. **Batch-first cost model**: no LLM calls in the request path of the web app. Expensive work runs on the scheduler. Orchestrator enforces a hard daily cost ceiling.
4. **Every model claim is backtested** (walk-forward, with transaction costs) and compared against naive + buy-and-hold baselines.
5. Raw data is never committed (see `.gitignore`).

## Conventions
- Python 3.11+, `ruff` + `pytest`; all written artifacts in English — code, comments, identifiers, `docs/`, and the final report (D12, 2026-06-13). The user converses in Vietnamese in chat; only files are English.
- LLM: DeepSeek V4 via the OpenAI-compatible SDK (`deepseek-v4-pro` reasoning agents, `deepseek-v4-flash` bulk sentiment) — D3 re-decided 2026-06-12 for cost. JSON mode + Pydantic validation; scheduler runs inside the off-peak window (16:30–00:30 UTC, −50%); frozen system prompts (no timestamps) to maximize automatic prefix caching. Per-agent model IDs are config, not code.
- Provider adapters behind interfaces (`PriceProvider`, `NewsProvider`) — free data sources break; swap adapters, not logic.
