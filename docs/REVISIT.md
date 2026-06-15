# RevBench — Revisit List (technical debt & deferred items)

> Things consciously deferred or simplified, to review **right after Phase 4**.
> Severity: 🔴 blocks the research conclusion · 🟠 quality/correctness · 🟢 nice-to-have.
> Keep this current — add a row whenever something is deferred, tick it when done.

## 🔴 Blocks the central research question ("do agents add alpha?")

| # | Item | Why it matters | Likely fix |
|---|---|---|---|
| R1 | **Agent-signal history is one day** (`as_of=2026-06-11`) | The fusion backtest (PLAN 4.5) needs months of agent signals; one snapshot can't be walk-forward tested | Run the scheduler daily to accumulate, OR backfill reasoning signals point-in-time over historical dates (expensive: ~45 LLM calls/day × N days) |
| R2 | **News history only ~1 month deep** | RSS + GDELT only return recent articles, so any news/sentiment feature is empty for ~99% of the 2-year price backtest window. **Empirically confirmed 2026-06-13: `python -m ml.features.sentiment` returns n=0** — all scored news is newer than the last date with a computable 5-day forward return (prices end 2026-06-11, news is June 9–14), so there is literally zero overlap yet | Accumulate forward via the scheduler; consider a one-off historical news source (most are paid). Document as a hard limitation if unsolved |
| R3 | **Sentiment `available_at` = compute time, not publication time** | All 708 articles were scored in one batch on 2026-06-13, so the stored `available_at` is "now" for all — wrong for a point-in-time backtest | The score is a pure function of the article text (temp=0), so its true availability is `published_at + 1 day`. Phase 4's sentiment feature derives availability from `published_at`, NOT from the sentiment row. Verify this assumption holds before trusting any IC number |

## 🟠 Correctness / quality

| # | Item | Why it matters | Likely fix |
|---|---|---|---|
| R4 | **EDGAR fundamentals mix 10-Q (quarterly) and 10-K (annual) values** | The QoQ comparison in `fundamentals_context` is noisy; the Fundamentals Agent already flagged an "unusual revenue spike" caused by this | Normalize to comparable periods: derive trailing-twelve-month or quarterly-only series; tag annual vs quarterly explicitly |
| ~~R5~~ | ~~**Agents not wired into the scheduler**~~ | ✅ **Done 2026-06-14.** `data_pipeline/scheduler.py` is now the composition root: `run_daily_pipeline` chains data → agents (sentiment + signals, budget-guarded, skipped without a key) → fusion (always, ML-only if no agent signals). `--once` runs it now; the cron job runs it nightly. This starts the R1/R2 history clock. | Done — let the scheduler run to accumulate history |
| R6 | **Fusion weights are hand-set, not learned** | PLAN 4.2 calls for weights learned from the backtest; learning them needs R1 history | Once history exists, fit the ensemble weights / a stacking model on the walk-forward folds |
| R7 | **LightGBM v1 underperforms buy & hold** (Sharpe 0.45 vs 1.17) | Expected per EMH, but the ML leg of the fusion is currently weak | Defer tuning until we know whether agents help; then revisit features/labels/model |
| R8 | **`reasoning_content` (full chain-of-thought) is discarded** | Only the short `rationale` field is stored; the richer reasoning could improve the "agent insights" UI | Capture `reasoning_content` from the v4-pro response into the signal payload (storage cost only) |

## 🟢 Nice-to-have / known limitations (documented, accept for now)

| # | Item | Note |
|---|---|---|
| R9 | **Survivorship bias** | Universe is today's fixed 15 blue-chips; stated as a limitation in the report (FINANCE_PRIMER §1.3) |
| R10 | **GDELT free API rate-limits hard (429)** | Job fails fast and self-heals next run; acceptable for a research project |
| R11 | **Streamlit UI needs the DB write-free** | DuckDB single-writer; run the dashboard when no batch job writes |
| R12 | **Open decisions D5 (frontend stack) & D10 (deployment)** | Not urgent; close before Phase 7 / Phase 8 |
| R13 | **AltData agents (Phase 5) not built** | Google Trends, Reddit, StockTwits, Wikipedia pageviews — planned for Phase 5 |

## Phase 4 specifically — review right after completion

- [ ] Re-read R1–R3: is the agent-alpha backtest conclusion honestly caveated everywhere it appears?
- [ ] Risk Agent + Strategist Agent (PLAN 4.3, 4.4) — built? They enrich the recommendation but aren't backtestable features.
- [ ] The IC number for the sentiment feature: is the sample size reported next to it every time?
- [ ] Did the fusion logic stay deterministic (reproducible recommendations)?
