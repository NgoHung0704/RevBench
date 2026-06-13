# RevBench — Decision Log

> Each entry is a still-open or already-closed choice. Format: context → options → Claude's recommendation → **status**. When you close one, change the status to ✅ with a date. 🔴 entries must be closed before the corresponding phase starts.

| ID | Topic | Needed before | Status |
|---|---|---|---|
| D1 | Price data source | Phase 1 | ✅ Closed 2026-06-12 |
| D2 | Storage layer | Phase 1 | ✅ Closed 2026-06-12 |
| D3 | LLM & cost strategy | Phase 3 | ✅ Closed 2026-06-12 (re-decided) |
| D4 | Agent framework | Phase 3 | ✅ Closed 2026-06-12 |
| D5 | Frontend stack | Phase 7 | 🟢 Open (not urgent) |
| D6 | Job scheduling | Phase 1 | ✅ Closed 2026-06-12 |
| D7 | Social/news data sources | Phase 1/5 | ✅ Closed 2026-06-12 |
| D8 | "Satellite data" — realistic scope | Phase 5 | ✅ Closed 2026-06-12 |
| D9 | Stock universe & prediction horizon | Phase 0 | ✅ Closed 2026-06-12 |
| D10 | Deployment | Phase 8 | 🟢 Open (not urgent) |
| D11 | Backtesting library | Phase 2 | ✅ Closed 2026-06-12 |
| D12 | Documentation/report language | Phase 0 | ✅ Closed 2026-06-13 |

---

## D1 — Price data source (market data provider)

**Context:** need daily OHLCV ≥ 5 years for ~15 US tickers, updated daily. Budget: ~€0.

| Option | Pro | Con |
|---|---|---|
| **yfinance** (scrapes Yahoo) | Free, no key, long history, has fundamentals | Unofficial, breaks when Yahoo changes; not for real production |
| **Finnhub** free tier | Official API, 60 calls/min, has news + fundamentals | Daily candle history limited on the free tier |
| **Alpha Vantage** free | Official, good daily-adjusted | 25 requests/day (very tight) |
| **Polygon.io** free | High quality | 5 calls/min, delayed, 2 years of history |
| **Stooq / Tiingo** | Tiingo free is fairly generous (long history) | Tiingo needs a key, 50 symbols/hour limit |

**Recommendation:** **yfinance as the primary dev/backtest source + Tiingo or Finnhub as a second source for cross-checks**, all behind a `PriceProvider` interface so swapping sources is painless. Accept that yfinance breaks occasionally since this is a research project.

**Status:** ✅ Closed 2026-06-12 — yfinance primary (dev/backtest), Tiingo backup, all behind the `PriceProvider` interface.

---

## D2 — Storage layer

**Context:** ~15 tickers × 5 years of daily data is *small* (a few MB). News + signals are a bit larger. The web app needs fast reads.

| Option | Pro | Con |
|---|---|---|
| **DuckDB + Parquet** | Zero-ops, blazing fast for analytics, perfect for backtests, file-based, easy to back up | Not designed for many concurrent writers (web app writes) |
| **PostgreSQL (+ TimescaleDB)** | Production-standard, integrates well with FastAPI, multi-user | Must be operated (Docker), overkill for small data |
| **SQLite** | Simplest | Slower analytics than DuckDB, weaker concurrency |

**Recommendation:** **hybrid** — DuckDB/Parquet for research & backtests (ml/), PostgreSQL (Docker) for serving (signals, recommendations, users) from Phase 6. Before Phase 6, only DuckDB is needed. → Start with DuckDB, add Postgres later, don't pick both up front.

**Status:** ✅ Closed 2026-06-12 — DuckDB/Parquet for research & backtests; add PostgreSQL for serving from Phase 6.

---

## D3 — LLM & cost strategy

**History:** first closed (2026-06-12): Claude API — Opus 4.8 reasoning + Haiku 4.5 Batch, estimated $3–6/day. **Re-opened the same day** for cost reasons → switched to **DeepSeek V4** (launched 2026-04-24; pricing & features verified on the web 2026-06-12).

| Model | Input $/1M | Output $/1M | Role |
|---|---|---|---|
| `deepseek-v4-pro` | $0.435 (cache hit ~$0.004) | $0.87 | News, Fundamentals, Technical, Risk, Strategist |
| `deepseek-v4-flash` | $0.14 (cache hit ~$0.003) | $0.28 | Bulk sentiment (hundreds of articles/night) |

Versus Claude: input ~11× cheaper, output ~29×. New estimate: **~$0.15–0.30/day ≈ $3–6/month** (old: $60–130/month).

DeepSeek-side cost levers:
- **Off-peak −50%** in 16:30–00:30 UTC — the 22:30 Paris job (= 20:30/21:30 UTC) sits inside the window; replaces the role Anthropic's Batch API played.
- **Automatic prefix caching** (cache hit ~97–99% cheaper) — the "frozen system prompt" rule stays.
- **OpenAI-compatible API**: `openai` SDK + `base_url=https://api.deepseek.com` — no separate SDK.
- JSON mode + function calling: structured outputs via Pydantic validation + retry on parse failure.

Accepted trade-offs (noted in the report):
1. **Reasoning below Opus 4.8** — measurable in the Phase 4 ablation; the model ID is config (see D4) so upgrading/changing a single agent is cheap.
2. **Loses Anthropic's server-side web search** → the News Agent reads only the internal store (RSS + GDELT — already built in Phase 1; reduces external dependency).
3. **Data passes through DeepSeek servers (China)** — we only send public data (prices, news), no PII; acceptable for a research project.

**Status:** ✅ Re-closed 2026-06-12 (user's decision) — DeepSeek V4: `deepseek-v4-pro` reasoning + `deepseek-v4-flash` sentiment, run in the off-peak window; budget ceiling lowered to `AGENT_DAILY_BUDGET_USD=1`.

**Update 2026-06-13 — A/B Flash vs Pro for Sentiment** (`python -m agents.compare`, 10 articles, max_tokens 1024): the two models agree closely (mean |Δscore| ≈ 0.10); Pro is actually *more compressed* on strong headlines (NVDA "exploding higher": Flash +0.60 vs Pro +0.15) and 8× pricier ($0.0048 vs $0.0006). → **Keep Flash for sentiment.** Side finding: single-shot scoring is noisy run-to-run → set `temperature=0` for sentiment so it's reproducible (same article → same score, no rewriting of backtest history on re-runs).

---

## D4 — Agent framework

| Option | Pro | Con |
|---|---|---|
| **OpenAI SDK direct** (DeepSeek's compatible endpoint) | No extra dependency, full control, easy to debug, prompt caching/off-peak used directly | Write your own orchestration (but ours is simple: fan-out → gather) |
| LangGraph / LangChain | Many ready-made patterns | Thick abstraction, hard to debug, API churns constantly, hides caching details |
| Managed Agents / heavyweight agent frameworks | The provider runs the agent loop | Overkill — our agents run a scheduled batch, no need for session containers |

**Recommendation:** **OpenAI SDK directly** (pointed at DeepSeek). RevBench's orchestration is a simple scheduled DAG — a heavy framework only adds risk. Revisit if we later need complex multi-turn conversations between agents.

**Status:** ✅ Closed 2026-06-12 — OpenAI-compatible SDK directly, no middleware framework.

---

## D5 — Frontend stack 🟢

| Option | Pro | Con |
|---|---|---|
| **Next.js + Tailwind + shadcn/ui + lightweight-charts** | Beautiful, industry-standard, SSR, good financial-chart ecosystem | Learning curve if new to React |
| Vite + React SPA | Lighter than Next | Handle routing/SSR yourself |
| Streamlit | Stand up in a day | Low aesthetic ceiling — won't meet the "beautiful UI" goal |

**Recommendation:** Next.js for the final product; Streamlit only as an internal temporary UI if an early demo is needed. **Question for the user:** are you already comfortable with React/TypeScript? If not, we could consider Vite+React (simpler than Next) — still can look great.

**Status:** 🟢 Fine to close before Phase 7.

---

## D6 — Job scheduling

| Option | Pro | Con |
|---|---|---|
| **APScheduler in one Python process** | Simplest, enough for one machine | No UI, not distributed |
| Prefect / Dagster | Nice observability, solid retries | Extra infrastructure to maintain |
| cron / Task Scheduler (Windows) | Zero code | Hard to manage dependencies between jobs |

**Recommendation:** APScheduler (with proper logging) for the whole project lifecycle; Prefect only if the pipeline genuinely grows.

**Status:** ✅ Closed 2026-06-12 — APScheduler in one process.

---

## D7 — Social/news data sources

**Harsh reality:** the X (Twitter) API read tier capable of pulling data costs $100+/month — the "Grok reads Twitter" idea is **out of budget**. Viable replacements:

| Source | Cost | Value |
|---|---|---|
| **Reddit API** (r/stocks, r/wallstreetbets, r/investing) | Free tier is enough | Retail sentiment — exactly where meme-stock sentiment lives |
| **StockTwits API** | Free public | Ticker-tagged sentiment ($AAPL tags) |
| **GDELT** | Free | Global news, massive coverage |
| **RSS** (Reuters, CNBC, Yahoo Finance, SeekingAlpha) | Free | Mainstream news |
| NewsAPI.org | Free tier 100 req/day, 24h delay | Convenient but limited |

**Recommendation:** RSS + GDELT (mainstream news) + Reddit + StockTwits (retail sentiment). Drop X/Twitter, state it clearly as a budget limitation in the report.

**Status:** ✅ Closed 2026-06-12 — RSS + GDELT + Reddit + StockTwits; drop X/Twitter (budget — noted as a limitation in the report).

---

## D8 — "Satellite data" — realistic scope

**Context:** the original idea — satellite imagery counting cars in Walmart parking lots, Google Maps foot traffic. Reality: commercial satellite imagery (Orbital Insight, RS Metrics) costs thousands of $/month; Google Maps "Popular Times" has no official API (scraping violates ToS).

**Free proxies with the same "measure real business activity" spirit:**

1. **Google Trends** — search interest for a brand/product (iPhone, Tesla Model Y…) → a proxy for consumer demand.
2. **Wikipedia pageviews** — an attention proxy, with academic studies showing correlation with volume.
3. **App-store rankings** — a traction proxy for consumer companies (Meta, Google apps).
4. **Job postings count** (career pages, levels.fyi trends) — a growth/contraction proxy.
5. (Stretch) **ESA's free Sentinel-2 imagery** — 10m resolution, enough for research-grade "port/factory activity" if we want a real satellite element in the report; but high effort, keep it a stretch goal.

**Recommendation:** 1–3 in Phase 5; item 5 only if time allows and we want a "wow factor" for the report.

**Status:** ✅ Closed 2026-06-12 — Google Trends + Wikipedia pageviews + app charts in Phase 5; Sentinel-2 is a stretch goal.

---

## D9 — Universe & prediction horizon

**Needs three things settled:**

1. **Universe:** are the 15 tickers proposed in PLAN 0.2 fine? (criteria: blue-chip, on Revolut, high liquidity, sector-diverse). Want to add European stocks on Revolut? (advice: not yet — adds timezone & data-source complexity).
2. **Horizon:** predict 1 day / 5 days / 20 days? **Recommendation: 5 days (one trading week)** — short enough to backtest many samples, long enough for news/fundamentals signals to "sink in" and for transaction costs not to eat all the alpha.
3. **Task:** direction classification (up/down — easy to evaluate, recommended) or price-level regression (much harder)?

**Status:** ✅ Closed 2026-06-12 — universe of 15 US tickers as proposed (no European stocks yet); horizon **5 trading days**; task **direction classification** (up/down).

---

## D10 — Deployment 🟢

Recommendation when the time comes: Docker Compose on a cheap local/VPS (Hetzner ~€5/month) or a free tier (frontend on Vercel, API on Railway/Fly.io). Decide after Phase 6.

---

## D11 — Backtesting library

| Option | Assessment |
|---|---|
| **Write our own walk-forward harness (pandas/numpy)** | Our problem is *signal evaluation* on a daily schedule — a self-written engine is ~300 lines, 100% understood, and great report material |
| vectorbt | Very fast but a steep API learning curve, the free version is limited |
| backtesting.py | Compact but oriented to single technical strategies, hard to fit multi-ticker ML signals |

**Recommendation:** write our own harness + use `quantstats` to produce nice metric reports.

**Status:** ✅ Closed 2026-06-12 — self-written walk-forward harness + `quantstats` for reporting.

---

## D12 — Documentation/report language

**Context:** docs were initially written in Vietnamese (the user's working language), with README + code + comments in English. The final report is submitted at INSA.

**Status:** ✅ Closed 2026-06-13 (user's decision) — **everything in English**: all `docs/` files, code, comments, and the final report. Vietnamese docs were translated to English on 2026-06-13. The user continues to communicate in Vietnamese in chat; only written artifacts are English.
