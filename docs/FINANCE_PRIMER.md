# RevBench — Finance Knowledge Roadmap (Finance Primer)

> This project stands on three legs: AI Engineering, Data Science, **and Finance**. A weak third leg makes the other two build something useless (or worse: something that *looks* profitable on a flawed backtest). This file is the learning roadmap + an anti-trap checklist.

## Block 1 — Required before Phase 2 (backtesting)

### 1.1 The Efficient Market Hypothesis (EMH) & why this problem is hard
- Prices already reflect public information → alpha from public data is *extremely thin*.
- Design implication: a directional accuracy of 52–55% is a *realistically good* target; anyone promising 80% is eating lookahead bias.
- Random walk & why "naive forecast" is the baseline you must beat.

### 1.2 Returns — work with returns, not prices
- Simple vs log returns; why models predict on returns rather than the price level (non-stationarity).
- Adjusted prices (split/dividend) — using the wrong one poisons features with garbage.
- The distribution of returns: fat tails, volatility clustering → don't assume Gaussian.

### 1.3 The four deadly biases (review checklist for every backtest PR)
| Bias | Meaning | Defense in RevBench |
|---|---|---|
| **Lookahead** | Using information that didn't exist at time t | The `available_at` column; features only from data ≤ t |
| **Survivorship** | The universe is only today's survivors | Accept it for blue-chips, *state the limitation* in the report |
| **Overfitting / data snooping** | Try 100 ideas, report the prettiest | Walk-forward; the final test set is touched once; log every experiment |
| **Transaction-cost ignorance** | Profit on paper, loss in real life | Simulate costs + slippage in every backtest |

### 1.4 Evaluation metrics
- Sharpe ratio (and why a Sharpe > 2 from public daily data should be treated with suspicion).
- Sortino, max drawdown, hit rate, profit factor, turnover.
- Information Coefficient (IC) — measures *signal* quality separately from the strategy.

## Block 2 — Before Phase 3–4 (agents & fusion)

### 2.1 Fundamental analysis (for the Fundamentals Agent)
- Reading a 10-K/10-Q: income statement, balance sheet, cash flow — only the "know where to look" level.
- Ratios: P/E, forward P/E, PEG, EV/EBITDA, gross/operating margin, FCF yield.
- Earnings season: the expectations game — prices move on the *surprise* (vs consensus), not the absolute number.

### 2.2 Technical analysis (for the Technical Agent)
- Momentum (the most academically supported phenomenon), mean reversion.
- RSI, MACD, Bollinger, moving averages, support/resistance, volume profile — understand the mechanism, don't worship it.
- Volatility regimes (low/high vol changes the behavior of every signal).

### 2.3 News & sentiment
- Event studies: prices react to news within minutes-to-hours → *yesterday's* news mostly predicts... volatility, not direction. Set the right expectation for the Sentiment Agent.
- Material event types: earnings, guidance, M&A, litigation, CEO change, rating up/downgrade, new product, macro (Fed, CPI).

### 2.4 Risk & position sizing (for the Risk Agent)
- Volatility targeting, fractional Kelly (and why full Kelly is suicidal).
- Correlation within a portfolio — 15 tech stocks ≠ diversification.
- Stop losses: academically debated, but the UX needs them.

## Block 3 — Advanced (if time allows / for the report)
- Factor models: CAPM → Fama-French 3/5 factors → momentum factor. Helps answer "is our alpha real, or just beta in disguise?".
- Basic market microstructure: bid-ask spread, why slippage exists.
- Alt-data literature: Da, Engelberg & Gao (2011) — Google Trends predictiveness; Moat et al. — Wikipedia pageviews; Bollen et al. (2011) — Twitter mood (and its replication critiques — read both sides!).

## Recommended reading
- **Advances in Financial Machine Learning** — Marcos López de Prado (the bible of doing financial ML right; the chapters on cross-validation for time series and backtest overfitting are required reading).
- **Quantitative Trading** — Ernest Chan (a pragmatic intro).
- Investopedia for individual concepts; SSRN for alt-data papers.

## Project culture rules
1. A backtest number without its methodology (window, costs, universe) = does not exist.
2. "Seems to work" is not a conclusion — IC, p-value, or silence.
3. A negative result (agents add no alpha) is still a good project result if the methodology is clean.
