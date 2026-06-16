# frontend

The RevBench web app (Phase 7) — Next.js 15 (App Router) + TypeScript + Tailwind +
TradingView lightweight-charts. Closes **D5**.

A premium, dark "financial-terminal-meets-editorial" UI: ink-and-gold palette,
Fraunces display serif + Manrope + JetBrains Mono for figures.

## Run

```powershell
npm install        # once
npm run dev        # http://localhost:3000
npm run build      # production build (prerenders all pages)
```

## Structure

- `src/app/page.tsx` — Dashboard: conviction board + agent signal matrix.
- `src/app/ticker/[symbol]/page.tsx` — per-ticker: candlestick, recommendation hero
  (action / score / confidence / thesis / counterarguments / risk), agent insights,
  scored news, fundamentals.
- `src/lib/mock.ts` — typed mock data shaped **exactly** like `ui/data.py`, using the
  real `ml.fusion` output for the 15 tickers. Swap this one module for calls to the
  FastAPI backend (Phase 6) and nothing else changes.
- `src/lib/types.ts` — the data contract (mirrors `agents/schemas.py` + `ml/fusion`).
- `src/components/` — design-system pieces (Badge, Meters, Sparkline, PriceChart,
  AgentInsight, TickerCard).

**Not financial advice** — disclaimer is persistent in the layout footer (hard rule).
