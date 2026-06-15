# RevBench — Master Plan

> This document is the source of truth for the roadmap. Each phase has a goal, deliverables, and a Definition of Done. Open technology choices are tagged `[D#]` and detailed in [DECISIONS.md](DECISIONS.md).

## Guiding principles

1. **Be honest about how hard this is.** Markets are close to efficient (Efficient Market Hypothesis). A realistic target: *directional accuracy* > 52–55% after transaction costs, or a Sharpe ratio better than buy-and-hold on a rigorous backtest — that already counts as a very good result. Every number must come from a **walk-forward backtest**, never from in-sample fitting.
2. **Baselines first, fancy later.** Always compare against the dumbest baseline (naive: "tomorrow = today", buy-and-hold). Any model/agent that fails to beat the baseline does not make it into the product.
3. **Separate the signal from the interface.** Data pipeline → model/agent → signal store → API → UI. Each layer is testable independently.
4. **Cost under control.** LLM agents run on a schedule (batch), not on every user request. Prompt caching + an off-peak window (−50%) for bulk work.
5. **Not financial advice.** A disclaimer on every user-facing surface.

---

## Roadmap overview

```
Phase 0  Foundation & decisions       ──┐
Phase 1  Data foundation (prices+news)  │  "Make the data flow"
Phase 2  Baseline ML + backtesting    ──┘
Phase 3  Agent system MVP             ──┐
Phase 4  Signal fusion + recommendation │  "Make the system smart"
Phase 5  Alt-data agents              ──┘
Phase 6  Backend API                  ──┐
Phase 7  Frontend web app               │  "Make it usable & beautiful"
Phase 8  Evaluation, hardening, report──┘
```

Rough total: ~12–16 weeks part-time (a school project), compressible if full-time. Phases 3–5 and 6–7 can partly run in parallel.

---

## Phase 0 — Foundation & decisions (1–2 weeks)

**Goal:** lock down the architectural decisions, set up the dev environment, learn the finance fundamentals.

| # | Task | Notes |
|---|---|---|
| 0.1 | Close the open decisions `[D1–D12]` | See [DECISIONS.md](DECISIONS.md) — **needs discussion with the user** |
| 0.2 | Lock the stock universe (~15 blue-chips tradable on Revolut) | Proposed: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, JPM, V, MA, KO, PG, JNJ, XOM, DIS |
| 0.3 | Repo setup: Python 3.11+, `uv`/`pip`, pre-commit, ruff, pytest; package structure | |
| 0.4 | Register API keys: data provider `[D1]`, DeepSeek, Reddit, … | Store in `.env` (never committed) |
| 0.5 | Study the finance primer — the "required before Phase 2" section | [FINANCE_PRIMER.md](FINANCE_PRIMER.md) |

**Done when:** every high-priority `[D#]` is closed; `pytest` is green on the skeleton; a demo script loads one year of AAPL prices.

---

## Phase 1 — Data foundation (2–3 weeks)

**Goal:** prices + news + fundamentals flow automatically into storage, clean and with quality checks.

| # | Task | Notes |
|---|---|---|
| 1.1 | Ingest daily OHLCV prices (+ intraday if the provider allows) for the whole universe | Provider per `[D1]`; store corporate actions (splits, dividends) — use **adjusted prices** |
| 1.2 | Ingest news: financial RSS feeds + GDELT/NewsAPI `[D7]` | Dedup, tag by ticker (simple keyword entity linking first) |
| 1.3 | Ingest fundamentals: quarterly reports (revenue, EPS, margins), earnings calendar | yfinance / SEC EDGAR (free, authoritative) |
| 1.4 | Storage layer `[D2]` + schema: `prices`, `news`, `fundamentals`, `signals` | Designed so backtests can't look ahead (every record carries an `available_at` timestamp) |
| 1.5 | Scheduler `[D6]`: daily job after the US close (22:00 CET) | Retry + alert on failure |
| 1.6 | Data-quality checks: missing days, outliers, unadjusted splits | Automated report |

**Done when:** one command → the whole universe has ≥ 5 years of clean prices + the last 30 days of news; the daily job runs itself.

**⚠️ Traps to avoid:** lookahead bias (using data that didn't exist at prediction time), survivorship bias (the universe is today's fixed set — accept it and state the limitation clearly in the report).

---

## Phase 2 — Baseline ML + backtesting engine (2–3 weeks)

**Goal:** have a rigorous evaluation framework BEFORE building anything smart. This is the most scientifically important phase.

| # | Task | Notes |
|---|---|---|
| 2.1 | Backtest engine `[D11]`: walk-forward (train on the past, test on the future, sliding window) | Simulate transaction costs (~0.1%/trade) + slippage |
| 2.2 | Standard metrics: directional accuracy, Sharpe, Sortino, max drawdown, hit rate, turnover — vs buy-and-hold | A `metrics.py` module reused forever |
| 2.3 | Baselines: naive (random walk), simple momentum (12-1), ARIMA | To know what the "floor" is |
| 2.4 | Feature engineering v1: returns, volatility, RSI, MACD, Bollinger, volume features, calendar features | All correctly lagged (use only data ≤ t to predict t+1) |
| 2.5 | ML model v1: **LightGBM/XGBoost** predicting P(price up) over a 1–5 day horizon | Tabular gradient boosting beats deep learning on most low-frequency financial problems — start here, not with an LSTM |
| 2.6 | (Stretch) Model v2: LSTM / Temporal Fusion Transformer for comparison | Only if v1 runs cleanly |

**Done when:** `python -m ml.backtest --model lgbm --universe all` prints a metrics table vs the baselines, reproducible (fixed seed).

---

## Phase 3 — Agent system MVP (2–3 weeks)

**Goal:** agents on DeepSeek V4 read news, score sentiment, interpret technicals & fundamentals, and emit a structured "agent signal" per ticker. Design detail: [AGENTS.md](AGENTS.md).

| # | Task | Notes |
|---|---|---|
| 3.1 | Agent framework: OpenAI-compatible SDK, JSON mode, structured outputs (Pydantic validation) `[D4]` | Model: `deepseek-v4-pro` for reasoning agents; `deepseek-v4-flash` for bulk sentiment `[D3]` |
| 3.2 | **News Agent**: summarize news per ticker (from the Phase 1 DB), extract material events | With source citations |
| 3.3 | **Sentiment Agent**: score per-article sentiment (−1..+1, confidence) on `deepseek-v4-flash` in the off-peak window | Structured JSON output, stored in `news_sentiment` |
| 3.4 | **Technical Agent**: take indicators from `ml/features`, interpret the technical state | The agent *interprets*, it does NOT compute the numbers — code computes them |
| 3.5 | **Fundamentals Agent**: read the latest earnings/filings, assess relative valuation | SEC EDGAR full-text |
| 3.6 | **Orchestrator**: run on the daily schedule, fan out agents in parallel, gather results | Prompt caching for system prompt + tool list |
| 3.7 | Logging & cost tracking: token usage, $ per run, store the reasoning trail | Hard daily budget ceiling, stop when exceeded |

**Done when:** `python -m agents.run --ticker AAPL` emits one JSON report: per-agent signal + summary + cost; runs daily for the whole universe under a fixed budget.

---

## Phase 4 — Signal fusion + recommendation engine (2 weeks)

**Goal:** blend the ML signal (Phase 2) + the agent signals (Phase 3) into a final recommendation: Buy/Hold/Sell + confidence + reasoning + risk.

| # | Task | Notes |
|---|---|---|
| 4.1 | `Recommendation` schema: action, confidence, horizon, expected range, rationale, risk flags | |
| 4.2 | Fusion v1: weighted ensemble (weights learned from the backtest) or stacking — the ML signal is the backbone, agent signals are extra features | **Backtestable** because agent signals are stored with history too |
| 4.3 | **Risk Agent**: check concentration, volatility regime, upcoming earnings, suggest position sizing (fractional Kelly / vol targeting) | |
| 4.4 | **Strategist Agent**: write the end-user explanation — concise, clear, honest about uncertainty | |
| 4.5 | Backtest the full fusion pipeline vs ML-only and the baselines | The central research question of the project: *do agents add alpha?* |

**Done when:** each ticker has one `Recommendation` per day in the DB, with a backtest table that proves (or honestly disproves) the value of the agent signals.

**Status (2026-06-14):** Fusion engine + `Recommendation` schema + store + CLI (`python -m ml.fusion`) done and live. **Risk Agent (4.3) + Strategist Agent (4.4) done** — they enrich each recommendation with position sizing/stops/risk flags and an honest user-facing thesis + counterarguments (run after fusion in the scheduler, shown on the dashboard). Sentiment feature + IC machinery (`python -m ml.features.sentiment`) done and tested. **4.5 — first measurable agent-alpha result (2026-06-14):** `python -m ml.backtest.altdata_study` folds the point-in-time Wikipedia attention feature into the walk-forward LightGBM. Over 491 OOS days it lifts Sharpe 0.45 → 0.62 (+0.18), accuracy 51.1% → 51.8%, and shrinks max drawdown — consistent with the feature's standalone IC of +0.025. This is the first measurable evidence an alt-data signal adds incremental value over the technical baseline. **Honest caveats:** still below buy & hold (Sharpe 1.17), one in-sample window (the +0.18 delta could be noise), thin IC — indicative, not conclusive; confirm across more history. The *news-sentiment* leg remains data-gated (IC `n=0`, R1/R2) until the scheduler (R5) accumulates history.

---

## Phase 5 — Alternative-data agents (2 weeks, cuttable)

**Goal:** add "Grok/satellite-style" data sources within a student budget. Reality: commercial satellite imagery & the X API are out of budget → use **free proxies** of equivalent research value. Detail: [DATA_SOURCES.md](DATA_SOURCES.md) `[D7][D8]`.

| # | Task | Source |
|---|---|---|
| 5.1 | Search-interest agent | Google Trends (pytrends), Wikipedia pageviews |
| 5.2 | Social agent | Reddit API (r/stocks, r/wallstreetbets), StockTwits public API |
| 5.3 | Consumer-traction agent | App-store rankings (public app charts), estimated web traffic |
| 5.4 | Evaluation: does each alt-data source have predictive power (information coefficient)? | Keep sources with stable IC > 0, drop the rest |

**Done when:** ≥ 2 alt-data sources are in the pipeline with a quantitative IC evaluation.

---

## Phase 6 — Backend API (1–2 weeks)

**Goal:** FastAPI serves the frontend; it does NOT run agents per request — it only reads precomputed results.

| # | Task |
|---|---|
| 6.1 | FastAPI + endpoints: `/tickers`, `/tickers/{t}/prices`, `/tickers/{t}/recommendation`, `/tickers/{t}/agents` (reasoning trail), `/portfolio/suggest` |
| 6.2 | Simple auth (API key / session) — enough for a demo |
| 6.3 | WebSocket/SSE to push updates when the daily job finishes |
| 6.4 | Auto-generated OpenAPI docs; tests for every endpoint |

---

## Phase 7 — Frontend web app (2–3 weeks)

**Goal:** a beautiful, easy-to-use interface `[D5]`.

| # | Task |
|---|---|
| 7.1 | Stack: Next.js + TypeScript + Tailwind + shadcn/ui; charts via TradingView **lightweight-charts** |
| 7.2 | Dashboard page: watchlist, recommendation heatmap, top movers |
| 7.3 | Ticker page: candlestick + signal overlay, recommendation card, an "Agent insights" tab showing each agent's reasoning (the product's differentiator) |
| 7.4 | Strategy page: portfolio-allocation suggestions + risk metrics |
| 7.5 | Dark mode, responsive, disclaimer banner |

**Progress tip:** if an early demo is needed, stand up a **Streamlit** UI in 1–2 days at the end of Phase 4, then replace it with Next.js in this phase.

---

## Phase 8 — Evaluation, hardening, report (1–2 weeks)

| # | Task |
|---|---|
| 8.1 | Paper-trading for 2–4 weeks: record recommendations ahead of time, compare against actual outcomes |
| 8.2 | Ablation study: ML-only vs ML+agents vs agents-only — the numbers table for the report |
| 8.3 | Hardening: error handling, rate limits, cost guard |
| 8.4 | Deployment `[D10]`: Docker Compose (db + api + frontend + scheduler) |
| 8.5 | Project report + demo video |

---

## Key risks & mitigations

| Risk | Mitigation |
|---|---|
| The model doesn't beat the baseline (very likely!) | Still a valid scientific result — report it honestly; the product still has value in its information aggregation & explanation |
| LLM cost over budget | Off-peak window, prompt caching, run daily instead of real-time, a hard budget ceiling in code |
| Free data provider dies / changes ToS (yfinance often does) | A `PriceProvider` abstraction layer — swap the source without touching the code above |
| Lookahead bias produces fake results | `available_at` timestamps on every record + the review checklist in FINANCE_PRIMER |
| Scope creep (satellite, real-time, options…) | Phase 5 is the first thing to cut; scope is locked to this PLAN |
