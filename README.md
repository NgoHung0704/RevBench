# RevBench

> **AI-powered decision-support system for blue-chip stocks tradable on Revolut.**
> Multi-agent intelligence (news, sentiment, fundamentals, technicals, alternative data) + ML forecasting + backtesting, served through a modern web app.

⚠️ **Disclaimer:** RevBench is a research / educational project (INSA Lyon — 4IF). It is **not financial advice**. Stock prediction is fundamentally hard (markets are close to efficient); the goal is a rigorous *decision-support* tool with honest, backtested performance metrics — not a money-printing machine.

## What it does (target state)

- 📈 **Forecasts** short-horizon price direction & ranges for ~15 blue-chip tickers (AAPL, MSFT, NVDA, …) with ML models validated by walk-forward backtesting.
- 🤖 **Agent swarm** built on the Claude API: agents that read news, score sentiment, parse SEC filings, compute technical signals, and mine alternative data (search trends, Reddit, web traffic) — then debate and fuse their views into one recommendation.
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
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest                          # unit tests (offline)
.\.venv\Scripts\python -m data_pipeline.fetch --all --years 5   # backfill prices
.\.venv\Scripts\python -m data_pipeline.jobs              # daily update once (prices+news+QC)
.\.venv\Scripts\python -m data_pipeline.scheduler         # keep running daily at 22:30 Paris
.\.venv\Scripts\python -m data_pipeline.quality           # data-quality report
```

Copy `.env.example` to `.env` and fill in keys as phases require them (Anthropic key needed from Phase 3).

## Status

✅ **Phase 0 — done (2026-06-12).** Core decisions closed in [docs/DECISIONS.md](docs/DECISIONS.md); skeleton installs, tests pass, price ingestion works end-to-end (yfinance → validation → DuckDB with `available_at`).

✅ **Phase 1 — Data foundation, done (2026-06-12).** Prices (5y × 15 tickers, validated), news (Yahoo per-ticker RSS + GDELT broad coverage), fundamentals (SEC EDGAR XBRL with point-in-time `available_at = filed + 1 day`), data-quality checks, `daily_update` job + APScheduler (22:30 Europe/Paris). Known limitation: GDELT's free API rate-limits per IP aggressively — the job fails fast on 429 and self-heals via overlapping 3-day windows on the next run.

🔜 **Phase 2 — Baselines + walk-forward backtesting engine** (next; the scientifically critical phase).
