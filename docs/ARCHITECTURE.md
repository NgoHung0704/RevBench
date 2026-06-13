# RevBench — System Architecture

## Overview diagram

```
                        ┌────────────────────────────────────────────┐
   DATA SOURCES         │              DATA PIPELINE                 │
                        │            (data_pipeline/)                │
 Prices (yfinance/…) ──▶│  ingestion ──▶ validation ──▶ storage      │
 News (RSS/GDELT)    ──▶│       every record carries `available_at`  │
 Fundamentals (EDGAR)──▶│                                            │
 Alt-data (Trends,   ──▶│   Storage: DuckDB/Parquet (research)       │
  Reddit, StockTwits)   │            PostgreSQL (serving, from P6)   │
                        └──────────────┬─────────────────────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      │
   ┌─────────────────────┐  ┌─────────────────────┐           │
   │      ML LAYER       │  │    AGENT LAYER      │           │
   │       (ml/)         │  │     (agents/)       │           │
   │ features ─▶ LightGBM│  │ Orchestrator        │           │
   │ walk-forward        │  │  ├─ News Agent      │◀─ DeepSeek V4
   │ backtest engine     │  │  ├─ Sentiment Agent │   (JSON mode, off-peak,
   │                     │  │  ├─ Technical Agent │    prefix caching)
   │  ml_signal(t,d)     │  │  ├─ Fundamentals Ag.│           │
   └─────────┬───────────┘  │  ├─ AltData Agent   │           │
             │              │  ├─ Risk Agent      │           │
             │              │  └─ Strategist Ag.  │           │
             │              │  agent_signals(t,d) │           │
             │              └─────────┬───────────┘           │
             │                        │                       │
             ▼                        ▼                       │
   ┌──────────────────────────────────────────────┐           │
   │           SIGNAL FUSION (ml/fusion)          │           │
   │  ensemble(ml_signal, agent_signals) ─▶       │           │
   │  Recommendation{action, confidence,          │           │
   │     horizon, rationale, risk}                │           │
   └─────────────────────┬────────────────────────┘           │
                         │  write to DB                       │
                         ▼                                    │
   ┌──────────────────────────────────────────────┐           │
   │         BACKEND API (backend/, FastAPI)      │           │
   │  REST + SSE  — only READS precomputed results│           │
   └─────────────────────┬────────────────────────┘           │
                         ▼                                    │
   ┌──────────────────────────────────────────────┐           │
   │      FRONTEND (frontend/, Next.js)           │           │
   │  Dashboard / Ticker / Agent insights /       │           │
   │  Strategy + disclaimer                       │           │
   └──────────────────────────────────────────────┘           │
                                                              │
   SCHEDULER (APScheduler): daily 22:30 Europe/Paris ─────────┘
   pipeline ▶ ml predict ▶ agents ▶ fusion ▶ notify
```

## Architectural principles

1. **Batch-first.** Everything expensive (LLM, ML inference) runs on a schedule after the US market close. The web app only reads results — instant response, predictable cost, never an LLM call on a user request.
2. **Point-in-time correctness.** Every table has an `available_at` column. Backtests may only read data with `available_at <= t`. This is the front line against lookahead bias — violating it makes the research result meaningless.
3. **Agents interpret, code computes.** The LLM never computes an RSI or an average — `ml/features` computes the numbers and the agent receives them to *interpret/reason about*. LLMs are great at language & synthesis, weak at arithmetic.
4. **Every signal is stored with history** (agent outputs included) → agent signals are backtestable like any other feature, which answers "do agents add alpha?".
5. **Provider abstraction.** `PriceProvider`, `NewsProvider` are interfaces — when a free source dies, swap the adapter, don't touch the logic.

## Directory layout (target)

```
RevBench/
├── data_pipeline/          # ingestion + validation + storage adapters
│   ├── providers/          #   yfinance_provider.py, finnhub_provider.py, ...
│   ├── news/               #   rss.py, gdelt.py, reddit.py, stocktwits.py
│   ├── fundamentals/       #   edgar.py
│   ├── store.py            #   DuckDB/Postgres adapters
│   └── jobs.py             #   jobs for the scheduler
├── ml/
│   ├── features/           #   technical, calendar, news-derived features
│   ├── models/             #   lgbm.py, baselines.py, (lstm.py)
│   ├── backtest/           #   walk-forward harness, metrics.py
│   └── fusion/             #   ensemble of ML + agent signals
├── agents/
│   ├── orchestrator.py     #   fan-out/gather, cost guard
│   ├── roster/             #   news.py, sentiment.py, technical.py, ...
│   ├── schemas.py          #   Pydantic schemas for structured outputs
│   └── prompts/            #   system prompts (version-controlled)
├── backend/
│   └── app/                #   FastAPI: routers, services, db
├── frontend/               #   Next.js app
├── notebooks/              #   research, EDA — never imported by production code
├── tests/
└── docs/                   #   this documentation
```

## Daily flow (when complete)

```
22:30 Europe/Paris  Scheduler tick (after NYSE closes 22:00 Paris)
  1. data_pipeline: fetch EOD prices, the day's news, alt-data       (~5 min)
  2. ml: compute features, predict P(up over 5 days)                 (~1 min)
  3. agents: score sentiment on all new articles in the off-peak window (~30–60 min, async)
  4. agents: orchestrator runs the deep per-ticker analysis          (parallel, ~10 min)
  5. fusion: blend signals → Recommendation, write to DB
  6. backend: emit "new data" SSE; the frontend refreshes itself
  7. cost report: log the day's token + $ usage vs the budget ceiling
```
