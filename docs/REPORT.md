# RevBench — Project Report

> **Working draft.** INSA Lyon — 4IF research project. Final report due D12 (2026-06-13 milestone in `docs/PLAN.md`); this is the living skeleton, filled where results exist and marked `TODO` where they are still accumulating.
>
> ⚠️ **Not financial advice.** RevBench is a research / educational system. Every figure here is a backtested or model-generated estimate, not investment guidance.

---

## Abstract

RevBench is an AI decision-support system that produces one explainable Buy / Hold / Sell recommendation per day for ~15 blue-chip stocks tradable on Revolut. It fuses a gradient-boosted machine-learning forecaster with a swarm of LLM agents (news, sentiment, technicals, fundamentals, risk, strategy) under a strict point-in-time discipline, and validates every claim with walk-forward backtesting against naive and buy-and-hold baselines. The central research question is **not** "can we beat the market" — markets are close to efficient — but **"do LLM agents add measurable, point-in-time predictive value on top of a price/technical ML baseline?"** This report documents the system, the methodology, the honest results to date, and the limitations.

**Headline findings (to date):**
- The ML baseline (LightGBM) **underperforms equal-weight buy-and-hold** in the test window — expected under the efficient-market hypothesis, and reported honestly rather than hidden.
- The first **measurable alternative-data signal** is Wikipedia attention: information coefficient (IC) ≈ **+0.025** over ~18k samples, which lifts backtest Sharpe from **0.45 → 0.62** (indicative, one window).
- The **agent-alpha question remains data-gated**: the news-sentiment IC is currently `n = 0` because scored-news history is shorter than one forward-return horizon. A nightly scheduler now accumulates point-in-time history to resolve this. *(TODO: ablation table once ≥ N weeks of history exist.)*

---

## 1. Introduction

### 1.1 Problem & motivation
TODO — short narrative: retail investors on Revolut have access to ~blue-chip equities but little rigorous, explainable decision support; commercial tools are opaque or expensive; we build an honest, backtested research tool.

### 1.2 Scope & non-goals
- **Universe:** 15 large-cap US names — AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, V, MA, KO, PG, JNJ, XOM, DIS.
- **Horizon:** short-horizon directional forecast (see `docs/DECISIONS.md` D9).
- **Non-goals:** no live trading, no intraday data, no personal-data handling, no claim of market-beating returns.

### 1.3 Research question
Does adding LLM-agent signals (interpreting news, filings, technicals, alternative data) to a price-based ML model improve out-of-sample, point-in-time forecast quality versus the ML model alone and versus naive baselines?

---

## 2. Background

### 2.1 Efficient markets & honest expectations
TODO — EMH (weak/semi-strong); why beating buy-and-hold is hard; why "the harness is the deliverable".

### 2.2 Point-in-time correctness (the central invariant)
Every stored record carries an `available_at` timestamp — the moment the information could first have been known. Backtests may only read rows with `available_at <= t`. This rules out look-ahead bias (the most common way backtests lie). Concrete rules: prices become known at the NYSE close; SEC filings at `filed + 1 day`; sentiment scores at `published_at + 1 day` (the score is a pure function of the article text). The full bias checklist lives in `docs/FINANCE_PRIMER.md` §1.3.

### 2.3 Known biases & how we address them
| Bias | Mitigation |
|---|---|
| Look-ahead | `available_at` gating on every read |
| Survivorship | Fixed present-day universe — stated as a limitation (§9) |
| Label overlap | Embargo / purging = horizon + 1 in walk-forward CV |
| Transaction costs | 10 bps/side modelled; skip-a-day execution (decide at close t, fill at close t+1) |

---

## 3. System Architecture

```
data_pipeline → DuckDB (point-in-time store) → ml/features → ml/models + ml/backtest
                         │                                        │
                    agents (LLM)  ─────────────► ml/fusion ──► recommendations
                         │                                        │
                    scheduler (nightly, off-peak)         backend (FastAPI, read-only)
                                                                  │
                                                            frontend (Next.js) ← Caddy
```

- **Batch-first:** no LLM calls in the web request path. All expensive work runs on the scheduler; the API and web app only read precomputed results.
- **Agents interpret, code computes:** LLMs never compute indicators or statistics (`ml/features` does); agent outputs are structured JSON (Pydantic-validated) and always persisted.
- **Provider abstraction:** free data sources break, so price/news/alt-data sit behind interfaces (`PriceProvider`, `NewsProvider`, `AltDataProvider`) — swap adapters, not logic.

See `docs/ARCHITECTURE.md` and `docs/AGENTS.md` for detail.

---

## 4. Data Sources

| Domain | Active source (free) | `available_at` rule | Notes |
|---|---|---|---|
| Prices | yfinance | NYSE close (21:00 UTC) | 5y × 15 tickers, validated |
| News | Yahoo per-ticker RSS + GDELT | `published_at + 1 day` | GDELT rate-limits (429) → self-heals |
| Fundamentals | SEC EDGAR XBRL | `filed + 1 day` | quarterly, restated-period dedup by latest filing |
| Alt-data (attention) | Wikipedia pageviews (Wikimedia API) | day + 1 | Google Trends bot-blocked → adapter swapped (R14) |

Provider choices and trade-offs: `docs/DATA_SOURCES.md` (`D1`, `D7`, `D8`).

---

## 5. Methodology

### 5.1 Features
17 causal technical features (returns, volatility, momentum, etc.) computed in `ml/features`, all strictly point-in-time. Plus an abnormal-attention feature from Wikipedia pageviews, and a news-sentiment feature (point-in-time, currently data-gated).

### 5.2 Model
LightGBM classifier (`LGBMClassifier`) for short-horizon directional probability. Choice vs XGBoost discussed in `docs/DECISIONS.md`. *(TODO: hyperparameters, feature list table.)*

### 5.3 Backtesting harness
Walk-forward, expanding window, embargo = horizon + 1 (purges label overlap), 10 bps/side transaction costs, skip-a-day execution. Metrics: Sharpe, accuracy vs base rate, hit-rate, drawdown. Baselines: always-up, 12-1 momentum, equal-weight buy-and-hold. Run: `python -m ml.backtest --model all`.

### 5.4 Agents
DeepSeek V4 via the OpenAI-compatible SDK — `deepseek-v4-pro` (reasoning: news / technical / fundamentals / risk / strategist), `deepseek-v4-flash` (bulk sentiment). JSON mode + Pydantic validation + one corrective retry; frozen system prompts for prefix caching; scheduler runs in the off-peak window (16:30–00:30 UTC, −50%); a hard **$1/day cost ceiling** (CostGuard) with a per-call usage ledger. Roster and cost control: `docs/AGENTS.md`.

### 5.5 Fusion
Deterministic, confidence-weighted blend of the ML probability and agent signals into one Buy/Hold/Sell with a confidence, then enriched by Risk + Strategist agents (position sizing, stop-loss, risk flags, a prose thesis + counterarguments). `python -m ml.fusion`. *(TODO: learned fusion weights once history exists — R6.)*

### 5.6 Signal evaluation
Information Coefficient (Spearman rank correlation between a signal at `t` and the forward return) as the per-signal predictive-value metric, always reported with its sample size.

---

## 6. Results

> Reproduce: `python -m ml.backtest --model all` and `python -m ml.backtest.altdata_study`.

### 6.1 ML baseline vs buy-and-hold
First honest OOS result (491 days, 2024-06 → 2026-06): **nothing beats equal-weight buy-and-hold in this bull window.** B&H Sharpe **1.17**; LightGBM v1 Sharpe **0.45**, accuracy **51.1%** vs a **53.9%** up-move base rate. Expected under EMH; the rigorous harness is the contribution.

### 6.2 Alternative data — Wikipedia attention
Abnormal-attention IC ≈ **+0.025** over ~18k samples — small but **real and positive** (unlike the news IC). Folded into the walk-forward backtest, the attention feature lifts LightGBM **Sharpe 0.45 → 0.62** and accuracy **51.1% → 51.8%** over the 491 OOS days — the first measurable evidence an alt-data signal adds incremental value (still below buy-and-hold; one window; indicative not conclusive).

### 6.3 Agent alpha — data-gated
The news-sentiment IC is currently **`n = 0`**: all scored news is newer than the last date with a computable forward return, so there is zero overlap yet. The framework is built and tested; the verdict awaits accumulated history. **The nightly scheduler (live since 2026-06-20) is now accumulating point-in-time agent + news history.**

### 6.4 Ablation study — ML-only vs ML+agents vs agents-only
**TODO** — the headline numbers table. Blocked on §6.3 history accumulation (R1/R2). Target: ≥ a few weeks of nightly runs, then `python -m ml.backtest` across the three configurations.

### 6.5 Paper-trading
**TODO** — record recommendations ahead of time, compare to realized outcomes over 2–4 weeks (PLAN 8.1).

---

## 7. Implementation & Deployment

- **Stack:** Python 3.11+ (ruff + pytest), DuckDB; FastAPI backend (read-only over the store); Next.js 15 + TypeScript + Tailwind + lightweight-charts + Framer Motion frontend.
- **Containerisation:** Docker Compose. Production stack (`docker-compose.prod.yml`): a Caddy reverse proxy as the sole public entry (:80, HTTPS-ready), a Next.js frontend (localhost-bound), an internal-only FastAPI backend (DuckDB mounted read-only), and an opt-in `scheduler` writer behind a compose profile.
- **Live deployment:** Hetzner Cloud (CX23, 4 GB, EU), self-hosted; one-shot host bootstrap via `scripts/bootstrap.sh`. Reproducibility: raw data is never committed; the host rebuilds the store from free sources.
- **Engineering notes (bugs found only in real deployment):** the slim Python image omits `libgomp` (LightGBM runtime); a profile-gated scheduler image went stale and had to share the backend image; the UI had to be made null-safe against a missing `lastClose`. All fixed and documented in git history.

---

## 8. Discussion

TODO — interpret the results: the model trailing buy-and-hold is a *valid* result consistent with EMH; the value of the project is the honest, reproducible harness and the first measurable alt-data signal; the agent-alpha question is answerable only with accumulated point-in-time history (a structural data limitation, not a modelling failure).

---

## 9. Limitations

- **Survivorship bias** — fixed present-day universe (R9).
- **Short news history** — RSS/GDELT return only recent articles, so any news feature is empty for ~99% of the 2-year backtest window (R2). Hardest limitation; only solvable by forward accumulation or a paid historical source.
- **Single market regime** — the OOS window is one bull market; results are window-dependent.
- **Free-data fragility** — GDELT/Google-Trends rate-limit; mitigated by adapter swaps and self-healing jobs.
- **One-day agent snapshot at first** — backtesting agent alpha needs months of history (R1).

---

## 10. Conclusion & Future Work

TODO — summary. Future: complete the ablation once history accumulates; learn fusion weights (R6); add a second alt-data source (Reddit/StockTwits, R13); capture full agent reasoning for richer explanations (R8); longer paper-trading.

---

## Appendix

- **A. Decisions log** — `docs/DECISIONS.md` (D1–D12, all closed).
- **B. Revisit / technical-debt list** — `docs/REVISIT.md` (R1–R14).
- **C. Reproduction commands** — see `README.md`.
- **D. References** — TODO.
