# RevBench — Data-Source Catalog

> Evaluated on 4 criteria: cost, reliability, legality (ToS), expected predictive value. Status: ✅ in use, 🟡 under consideration, ❌ rejected (reason noted so we don't relitigate).

## 1. Prices & volume (Phase 1)

| Source | Cost | Notes | Status |
|---|---|---|---|
| yfinance (Yahoo) | Free | Unofficial, breaks often; long history, has adjusted close | ✅ primary dev source `[D1]` |
| Tiingo | Free tier | Official, long history, 50 symbols/h | 🟡 backup source |
| Finnhub | Free tier | 60 calls/min, includes news + fundamentals + earnings calendar | 🟡 versatile |
| Alpha Vantage | Free | 25 req/day — too tight | ❌ |
| Polygon.io free | Free | Only 2 years of history, 5 calls/min | ❌ for this need |

## 2. News (Phase 1, 3)

| Source | Cost | Notes | Status |
|---|---|---|---|
| RSS feeds (CNBC, Reuters, Yahoo Finance, MarketWatch, SeekingAlpha) | Free | Stable, legal, good real-time coverage | ✅ |
| GDELT 2.0 | Free | Huge coverage, queried via API; noisy, needs filtering | ✅ |
| NewsAPI.org | Free tier | 100 req/day, 24h delay on free | 🟡 secondary |
| Finnhub company news | Free tier | Ticker-tagged already — saves entity-linking work | ✅ if using Finnhub |
| Bloomberg/Reuters API | $$$$ | | ❌ budget |
| Server-side LLM web search | ~$10/1K searches + tokens | Dropped when moving to DeepSeek (D3) — the News Agent reads the internal store (RSS + GDELT) | ❌ |

## 3. Fundamentals (Phase 1, 3)

| Source | Cost | Notes | Status |
|---|---|---|---|
| SEC EDGAR (official API) | Free | 10-K/10-Q/8-K full text + XBRL standardized figures; 10 req/s rate limit | ✅ the gold source |
| yfinance fundamentals | Free | Convenient but figures sometimes off | 🟡 quick reference |
| Financial Modeling Prep | Narrow free tier | | 🟡 |

## 4. Social sentiment (Phase 5) `[D7]`

| Source | Cost | Notes | Status |
|---|---|---|---|
| Reddit API (PRAW) | Free tier | r/stocks, r/wallstreetbets, r/investing; 100 QPM is enough | ✅ |
| StockTwits public API | Free | Messages with cashtags + user-tagged sentiment | ✅ |
| X (Twitter) API | $100+/month for read | "Grok reads Twitter" — out of budget | ❌ budget (noted as a limitation in the report) |
| Facebook/Meta data | No suitable public API | | ❌ |

## 5. Alternative data (Phase 5) `[D8]`

| Source | Cost | Proxy for | Status |
|---|---|---|---|
| Google Trends (pytrends) | Free | Consumer demand by brand/product | ✅ |
| Wikipedia pageviews API | Free | Investor attention (literature-backed) | ✅ |
| App-store charts | Free (public) | Traction of consumer apps (META, GOOGL, …) | 🟡 |
| Job postings (career pages) | Free but must scrape | Headcount growth | 🟡 high effort |
| Google Maps Popular Times | No API; scraping violates ToS | Foot traffic | ❌ legal |
| Commercial satellite imagery (RS Metrics, Orbital Insight) | $$$$$ | Foot traffic, inventory | ❌ budget |
| ESA Sentinel-2 (free, 10m/pixel) | Free | Large-scale port/factory activity | 🟡 stretch goal "wow factor" |

## General rules

1. **Every record is stored with `available_at`** (the moment we *could* have known the information) — not `published_at` — so point-in-time backtests are correct.
2. **Respect ToS & rate limits** — a polite User-Agent for EDGAR, exponential backoff everywhere.
3. **Adapter pattern**: one class per source behind a shared interface; when a source dies, swap the adapter.
4. **Raw data is never committed to git** (already in `.gitignore`) — a script that re-downloads from scratch is itself a deliverable.
