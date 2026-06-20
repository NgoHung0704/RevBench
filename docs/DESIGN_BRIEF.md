# RevBench — Design Brief / Prompt for a UI Design Agent

> Paste this whole document as the prompt. It is self-contained but points to real
> files; read those first so the design *evolves* the existing app rather than
> replacing a product you haven't seen.

---

## 0. Your role

You are a senior product designer + front-end engineer. Your job is to elevate the
RevBench web app into a **beautiful, professional, trustworthy** interface with a
**modern, gentle, fluid motion system** — without breaking the data contracts or
the research ethos below. Deliver working Next.js + Tailwind code, not mockups.

Bias to **restraint and polish over novelty**. This is a finance research tool, not
a landing page: motion should feel *calm and precise*, never playful or attention-
seeking. Think Linear / Vercel / Stripe dashboards and the Bloomberg-terminal lineage
— confident, quiet, fast.

## 1. What RevBench is (context you must respect)

An AI decision-support dashboard for ~15 blue-chip stocks (AAPL, MSFT, NVDA, AMZN…).
A multi-agent system (news / technical / fundamentals reasoning agents + sentiment +
risk + strategist) plus an ML model produce **one Buy / Hold / Sell recommendation
per ticker**, each with a confidence, risk sizing, and an honest written thesis +
counterarguments.

Non-negotiable product values — the design must reinforce, never undermine, these:

- **Not financial advice.** A clear disclaimer must be visible on every screen
  (a persistent, tasteful banner or footer — present but not alarming).
- **Intellectual honesty is the brand.** The model currently *underperforms buy &
  hold*, and some signals are data-gated (sample size `n=0`). The UI must show
  confidence, sample sizes, and caveats *as first-class content*, not hide them.
  Never design anything that implies certainty or "get rich" energy.
- **Batch-first.** All numbers are precomputed; the UI only *reads* them. No live
  tickers, no fake real-time pulsing, no streaming-price theatrics. Freshness is
  shown via an "as of <date>" stamp, honestly.

## 2. What already exists (read these first, then improve)

Stack — keep it: **Next.js 15 (App Router, RSC, TypeScript) + Tailwind + TradingView
lightweight-charts**. Server components fetch from a FastAPI backend.

Read, in order:
- `frontend/src/lib/types.ts` — the exact data you have to design around (below).
- `frontend/src/app/globals.css` — the current "ink-and-gold" design tokens.
- `frontend/tailwind.config.ts` — the token wiring.
- `frontend/src/app/page.tsx` — the Dashboard.
- `frontend/src/app/ticker/[symbol]/page.tsx` — the ticker detail page.
- `frontend/src/components/*` — TickerCard, Badge, Meters, Sparkline, PriceChart,
  AgentInsight, ApiDown.

**Current design language (your starting point, evolve it — don't discard it):**
a dark "financial-terminal-meets-editorial" theme. Ink background with faint ambient
gold/green radial glows; glass `.card`s (rounded-2xl, subtle inset + deep soft
shadow, backdrop-blur); a warm **gold** accent (`--gold`); semantic **green/red/gray**
for buy/sell/hold; tabular-nums monospace for every number. It already looks good
**but it is almost entirely static** — your headline contribution is **motion** plus
a tightening of hierarchy, spacing, and the chart experience.

## 3. The data you design around (do not invent fields)

```ts
TickerSummary = { stock{ticker,name,sector}, rec, prices: Bar[], lastClose, change1d }
Recommendation = { action: buy|hold|sell, score, confidence[0..1], mlProba,
  components{ml,news,technical,fundamentals},   // signed contributions, drive a breakdown viz
  riskLevel: low|moderate|high, maxPositionPct, stopLossPct, riskFlags[],
  thesis: string, counterarguments: string[], conviction: low|medium|high, asOf }
AgentSignal = { agent: news|technical|fundamentals, signal[-1..1], confidence[0..1],
  rationale?, summary?, regime?, valuation_view?, growth_view?, key_events?[],
  catalysts?[], red_flags?[] }
NewsItem = { date, title, score, confidence, event_type }
FundamentalRow = { metric, period_end, value, yoy|null, isEps? }
CostSummary = { today, total, calls }   // the daily LLM-budget meter
```

## 4. The two screens

**A. Dashboard** (`/`) — the "conviction board".
- A scannable grid of ticker cards: symbol, name, sparkline, last close + 1-day change,
  the recommendation (action chip + conviction + confidence). Sortable/filterable by
  action, conviction, sector.
- An "agent signal matrix" — tickers × {news, technical, fundamentals} as a calm
  heatmap of signed signals.
- The cost meter (today's spend vs the $1/day ceiling) shown subtly.
- The disclaimer.

**B. Ticker detail** (`/ticker/[symbol]`).
- A hero: the recommendation with action, conviction, confidence, the **strategist
  thesis** and **counterarguments** as readable editorial prose, plus risk sizing
  (max position %, stop-loss %, risk flags).
- A candlestick chart (lightweight-charts) with a clean range control.
- A signed **component breakdown** (ml / news / technical / fundamentals) — a small,
  honest contribution viz.
- "Agent insights": each agent's reasoning trail (the product's differentiator).
- Scored news list and a clean quarterly fundamentals table.
- The disclaimer.

## 5. Visual direction

- **Evolve the palette**, keep the spirit: ink + gold + semantic green/red/gray.
  You may refine tints, add 1–2 calm supporting hues, and design proper light-on-dark
  elevation. Keep contrast WCAG AA.
- **Typography:** an editorial sans for prose (thesis/counterarguments read like a
  short analyst note), a mono with tabular-nums for every figure. Strong size/weight
  hierarchy; generous line-height for the prose.
- **Depth & texture:** layered surfaces, hairline borders, soft shadows, the existing
  ambient glow — used sparingly. Avoid heavy glassmorphism everywhere; let it breathe.
- **Density:** information-dense but uncluttered. Align to an 8px grid. Numbers right-
  aligned in tables.

## 6. Motion system — the headline ask ("nhẹ nhàng & mượt mà")

Design a **coherent, reusable motion system**, not one-off animations. Principles:

- **Calm & physical.** Short, eased, purposeful. Nothing bounces hard, nothing spins,
  nothing loops forever. Motion should clarify state changes and spatial relationships,
  never decorate.
- **Timing:** micro-interactions **120–180ms**, entrances/transitions **220–320ms**,
  page-level **≤ 400ms**. Easing: a gentle ease-out / custom cubic-bezier (e.g.
  `cubic-bezier(0.22, 1, 0.36, 1)`); avoid linear and avoid heavy overshoot.
- **Where motion lives:**
  - Page/route transitions: a soft cross-fade + small upward translate (8–12px).
  - Card/list entrance: subtle staggered fade-up on first paint (stagger ≤ 40ms,
    capped so a 15-card grid doesn't feel slow).
  - Hover/focus: gentle lift (translateY + shadow + border-glow), 120ms.
  - Numbers that change (confidence meters, component bars, score): **count-up /
    width tween** on mount so the data "settles in".
  - Sparklines / the component breakdown: draw-in (path length or width) once,
    not on every render.
  - Skeleton → content: graceful fade swap (no harsh pop). Sensible loading states.
  - Chart range switch: smooth, not a hard redraw.
- **Discipline:** respect `prefers-reduced-motion` — drop to instant/opacity-only.
  Don't animate layout in a way that causes CLS. Keep everything 60fps (animate
  transform/opacity, not top/left/width-of-layout where avoidable). Motion must never
  delay reading the recommendation — content is usable before animation finishes.
- **Suggested tooling:** Framer Motion (`motion`) for React — declarative, first-class
  `prefers-reduced-motion`, layout animations. Rationale vs alternatives: CSS-only is
  lightest but awkward for staggered/orchestrated entrances and shared-element route
  transitions; GSAP is powerful but heavier and overkill here. Use Framer for
  orchestration, plain CSS transitions for simple hovers. Keep the JS bundle lean.

## 7. Hard constraints (do not violate)

1. **Disclaimer on every screen.** "Not financial advice — research/education only."
2. **No invented data, no fake live data.** Design only for the fields in §3; honor
   `as of <date>`; no streaming/real-time effects.
3. **Show honesty:** always pair a metric with its confidence/sample size where the
   data has one. Surface `riskFlags`, `counterarguments`, and low-conviction states
   prominently — don't bury them.
4. **Accessibility:** WCAG AA contrast, full keyboard nav, visible focus rings,
   `prefers-reduced-motion`, semantic HTML, alt/aria on charts.
5. **Performance:** fast first paint (RSC), lean client JS, no layout thrash, 60fps
   motion, graceful `ApiDown` state when the backend is unreachable.
6. **Responsive:** great on a 13" laptop primarily; usable down to mobile.

## 8. Deliverables / definition of done

1. A short **design rationale**: palette + type scale + spacing + the motion system
   (durations, easing, the catalogue of interactions) and *why*.
2. Updated `globals.css` / `tailwind.config.ts` tokens (incl. motion tokens:
   durations, easings, named transitions).
3. Reworked **Dashboard** and **Ticker detail** plus the shared components, with the
   motion system applied consistently.
4. A reduced-motion pass and a basic a11y pass.
5. Notes on any new dependency (e.g. Framer Motion) and its bundle impact.

**Done when:** the app feels noticeably more premium and alive *and* still loads fast,
reads honestly, carries the disclaimer everywhere, and respects reduced-motion — with
zero invented data.
