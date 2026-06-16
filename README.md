# RevBench

> **AI-powered decision-support system for blue-chip stocks tradable on Revolut.**
> Multi-agent intelligence (news, sentiment, fundamentals, technicals, alternative data) + ML forecasting + backtesting, served through a modern web app.

⚠️ **Disclaimer:** RevBench is a research / educational project (INSA Lyon — 4IF). It is **not financial advice**. Stock prediction is fundamentally hard (markets are close to efficient); the goal is a rigorous *decision-support* tool with honest, backtested performance metrics — not a money-printing machine.

## What it does (target state)

- 📈 **Forecasts** short-horizon price direction & ranges for ~15 blue-chip tickers (AAPL, MSFT, NVDA, …) with ML models validated by walk-forward backtesting.
- 🤖 **Agent swarm** built on DeepSeek V4 (OpenAI-compatible API): agents that read news, score sentiment, parse SEC filings, interpret technical signals, and mine alternative data (search trends, Reddit, web traffic) — then fuse their views into one recommendation.
- 🧠 **Explainable recommendations**: Buy / Hold / Sell with confidence, risk metrics, and the full agent reasoning trail.
- 🖥️ **Web dashboard**: watchlist, charts, agent insights, strategy suggestions.

## Project map

| Path | Purpose |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | 📌 **Master roadmap** — phases, milestones, deliverables |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Open decisions to discuss (tech choices, trade-offs) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture & data flow |
| [docs/AGENTS.md](docs/AGENTS.md) | Agent system design (roster, tools, cost control) |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | Catalog of data sources, cost & feasibility |
| [docs/FINANCE_PRIMER.md](docs/FINANCE_PRIMER.md) | Finance domain knowledge roadmap & pitfalls |
| `data_pipeline/` | Ingestion: prices, news, fundamentals, alt-data |
| `ml/` | Features, models, backtesting |
| `agents/` | Claude-powered agent system |
| `backend/` | API server (FastAPI) |
| `frontend/` | Web app |
| `notebooks/` | Research & exploration |
| `tests/` | Test suite |

## Getting started

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev,ui]"
.\.venv\Scripts\python -m pytest                          # unit tests (offline)
.\.venv\Scripts\python -m data_pipeline.fetch --all --years 5   # backfill prices
.\.venv\Scripts\python -m data_pipeline.scheduler --once  # full pipeline once: data+agents+fusion
.\.venv\Scripts\python -m data_pipeline.scheduler         # schedule it nightly at 22:30 Paris
.\.venv\Scripts\python -m ml.fusion                       # recommendations only (ML+agents)
.\.venv\Scripts\streamlit run ui/streamlit_app.py         # temporary dashboard
```

The dashboard is read-only over the DuckDB store — run it when no batch job is writing.

Copy `.env.example` to `.env` and fill in keys as phases require them (`DEEPSEEK_API_KEY` needed from Phase 3).

### Deploy (Docker Compose)

The production surface is the FastAPI backend + Next.js web app. With a populated `data/revbench.duckdb` (build it via the pipeline commands above), bring up the stack:

```bash
docker compose up --build        # API on :8000, web on :3000
```

- **backend** mounts `./data` **read-only** and serves the API; **frontend** is a Next.js standalone image that fetches the API server-side over the compose network (`API_URL=http://backend:8000`).
- DuckDB is single-writer across processes ([R11](docs/REVISIT.md)), so the default stack is read-only. To also run the nightly `data → agents → fusion → enrichment` pipeline, set `DEEPSEEK_API_KEY` in `.env` and enable the writer profile:

```bash
docker compose --profile scheduler up   # adds the writer; expect brief API read blips while it holds the lock
```

## Status

✅ **Phase 0 — done (2026-06-12).** Core decisions closed in [docs/DECISIONS.md](docs/DECISIONS.md); skeleton installs, tests pass, price ingestion works end-to-end (yfinance → validation → DuckDB with `available_at`).

✅ **Phase 1 — Data foundation, done (2026-06-12).** Prices (5y × 15 tickers, validated), news (Yahoo per-ticker RSS + GDELT broad coverage), fundamentals (SEC EDGAR XBRL with point-in-time `available_at = filed + 1 day`), data-quality checks, `daily_update` job + APScheduler (22:30 Europe/Paris). Known limitation: GDELT's free API rate-limits per IP aggressively — the job fails fast on 429 and self-heals via overlapping 3-day windows on the next run.

✅ **Phase 2 — Backtesting engine + baselines, done (2026-06-12).** Walk-forward harness (expanding window, embargo = horizon+1 purging label overlap, 10 bps/side costs, skip-a-day execution), metrics module, 17 causal technical features, baselines (always-up, 12-1 momentum) + LightGBM v1. Run: `python -m ml.backtest --model all`.

First honest OOS result (491 days, 2024-06 → 2026-06): **nothing beats equal-weight buy & hold in this bull window** — B&H Sharpe 1.17; LightGBM v1 Sharpe 0.45 with 51.1% accuracy vs a 53.9% up-move base rate. Expected per EMH; the harness is the deliverable. Whether agent signals add alpha is exactly Phase 3–4's research question.

🟡 **Phase 3 — Agent system MVP, nearly done.** Live on DeepSeek V4: Sentiment Agent (`deepseek-v4-flash`, 708 articles scored) + three reasoning agents (News / Technical / Fundamentals on `deepseek-v4-pro`) run by an orchestrator that fans out per ticker and stores `agent_signals`. Infra: JSON mode + Pydantic + one corrective retry, per-call cost accounting, `agent_usage` ledger + hard $1/day budget guard. CLI: `python -m agents.run --task {sentiment,signals} [--dry-run]`. Verified live on AAPL (news/technical/fundamentals all produce sensible, reasoned signals). Remaining: weekly AltData agent (Phase 5) + wiring agents into the scheduler.

🟢 **Temporary dashboard (Streamlit).** `streamlit run ui/streamlit_app.py` — overview heatmap of agent signals across the universe, plus per-ticker candlestick, the agent reasoning trail (News/Technical/Fundamentals), scored news, and fundamentals. Read-only over the precomputed store; replaced by the Next.js app in Phase 7 (D5).

🟡 **Phase 4 — signal fusion, in progress.** Deterministic fusion of the ML probability + agent signals into one Buy/Hold/Sell per ticker (`python -m ml.fusion`), stored and shown on the dashboard. Point-in-time news-sentiment feature + Information Coefficient machinery (`python -m ml.features.sentiment`). **Honest status:** the central question — *do agents add alpha?* — is **data-gated**: the sentiment IC is currently `n=0` because all scored news (June 9–14) is newer than the last date with a computable 5-day forward return (prices end June 11). The framework is built and tested; the verdict waits for the scheduler to accumulate history. **Risk + Strategist agents done** — each recommendation now carries position sizing, stops, risk flags, and an honest prose thesis + counterarguments (shown on the dashboard). Deferred items tracked in [docs/REVISIT.md](docs/REVISIT.md).

🟡 **Phase 5 — alt-data, started.** Wikipedia pageviews as an attention proxy via the official Wikimedia API (5y daily history, behind an `AltDataProvider` interface). `python -m data_pipeline.altdata.fetch --source wikipedia --all` then `python -m ml.features.altdata`. **First measurable alt-data signal:** abnormal-attention IC ≈ **+0.025 over 18k samples** — small but real and positive, unlike the news IC (`n=0`). (A Google Trends provider is built too, but its free endpoint is bot-blocked — R14.) Folded into the walk-forward backtest (`python -m ml.backtest.altdata_study`): adding the attention feature lifts LightGBM **Sharpe 0.45 → 0.62** and accuracy 51.1% → 51.8% over 491 OOS days — the first measurable evidence an alt-data signal adds incremental value (still below buy & hold, one window, indicative not conclusive). Remaining: Reddit / StockTwits.

✅ **Phase 6 — FastAPI backend.** Read-only HTTP over the DuckDB store (reuses `ui/data.py`; no LLM in the request path) serving JSON shaped exactly like the frontend types: `/api/universe`, `/api/tickers/{symbol}`, `/api/cost`. Verified live on the real DB (15 tickers; AAPL detail = 180 bars + 3 agent signals + 12 news + 18 clean quarterly fundamentals + the real strategist thesis). `python -m uvicorn backend.app.main:app`. Next: point the frontend at it (replace `mock.ts` with fetches — same shapes).

✅ **Phase 7 — web app (D5 closed).** A premium Next.js 15 + TypeScript + Tailwind + lightweight-charts frontend in [frontend/](frontend/) — dark "financial-terminal-meets-editorial" theme, Dashboard (conviction board + agent signal matrix) and per-ticker pages (candlestick, recommendation hero with the strategist thesis + counterarguments + risk sizing, agent insights, scored news, fundamentals). **Wired live to the FastAPI backend** (`src/lib/api.ts`, server-side fetch, `force-dynamic`); falls back to a graceful "API unavailable" panel when the backend is down. `cd frontend && npm install && npm run dev`.

✅ **Phase 8 — deployment (D10 closed, 2026-06-16).** Docker Compose stack ([docker-compose.yml](docker-compose.yml)): a `backend` image (Python 3.12, `.[api]`) mounting the DuckDB **read-only** + a `frontend` image (Next.js standalone) talking to it over the compose network, plus an opt-in `scheduler` profile for the nightly writer. Both images build clean and the stack was verified end-to-end (real data DuckDB → API → web, 15 tickers rendered, no fallback panel). See [Deploy](#deploy-docker-compose).
