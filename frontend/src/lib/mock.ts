import type {
  AgentSignal,
  Bar,
  FundamentalRow,
  NewsItem,
  Recommendation,
  Stock,
  TickerData,
} from "./types";
import type { Action } from "./utils";

// NOTE: mock data shaped exactly like ui/data.py. The recommendation numbers
// below are the REAL output of `python -m ml.fusion` on 2026-06-11 — so the
// dashboard shows authentic signals, not invented ones. Swap this module for
// real API calls when the FastAPI backend (Phase 6) exists.

export const UNIVERSE: Stock[] = [
  { ticker: "AAPL", name: "Apple", sector: "Technology" },
  { ticker: "MSFT", name: "Microsoft", sector: "Technology" },
  { ticker: "NVDA", name: "NVIDIA", sector: "Semiconductors" },
  { ticker: "GOOGL", name: "Alphabet", sector: "Communication Services" },
  { ticker: "AMZN", name: "Amazon", sector: "Consumer Discretionary" },
  { ticker: "META", name: "Meta Platforms", sector: "Communication Services" },
  { ticker: "TSLA", name: "Tesla", sector: "Consumer Discretionary" },
  { ticker: "JPM", name: "JPMorgan Chase", sector: "Financials" },
  { ticker: "V", name: "Visa", sector: "Financials" },
  { ticker: "MA", name: "Mastercard", sector: "Financials" },
  { ticker: "KO", name: "Coca-Cola", sector: "Consumer Staples" },
  { ticker: "PG", name: "Procter & Gamble", sector: "Consumer Staples" },
  { ticker: "JNJ", name: "Johnson & Johnson", sector: "Healthcare" },
  { ticker: "XOM", name: "Exxon Mobil", sector: "Energy" },
  { ticker: "DIS", name: "Walt Disney", sector: "Communication Services" },
];

type Raw = {
  action: Action;
  score: number;
  confidence: number;
  ml: number;
  news: number;
  technical: number;
  fundamentals: number;
  price: number;
};

// real fusion output (ticker -> legs) + a representative price level
const RAW: Record<string, Raw> = {
  AMZN: { action: "buy", score: 0.38, confidence: 0.61, ml: 0.56, news: 0.35, technical: -0.1, fundamentals: 0.2, price: 213 },
  XOM: { action: "buy", score: 0.37, confidence: 0.66, ml: 0.47, news: 0.35, technical: 0.2, fundamentals: 0.0, price: 118 },
  JNJ: { action: "buy", score: 0.34, confidence: 0.69, ml: 0.35, news: 0.15, technical: 0.7, fundamentals: -0.1, price: 156 },
  KO: { action: "buy", score: 0.2, confidence: 0.31, ml: -0.02, news: 0.4, technical: 0.6, fundamentals: 0.2, price: 71 },
  JPM: { action: "hold", score: 0.12, confidence: 0.2, ml: -0.05, news: -0.2, technical: 0.6, fundamentals: 0.2, price: 268 },
  MA: { action: "hold", score: 0.08, confidence: 0.13, ml: -0.11, news: 0.8, technical: -0.4, fundamentals: -0.1, price: 525 },
  PG: { action: "hold", score: 0.06, confidence: 0.11, ml: -0.03, news: -0.1, technical: 0.4, fundamentals: 0.1, price: 166 },
  META: { action: "hold", score: 0.03, confidence: 0.04, ml: 0.28, news: -0.3, technical: -0.6, fundamentals: 0.2, price: 695 },
  V: { action: "hold", score: 0.01, confidence: 0.03, ml: -0.04, news: 0.5, technical: -0.5, fundamentals: 0.2, price: 352 },
  AAPL: { action: "hold", score: 0.01, confidence: 0.01, ml: -0.2, news: 0.15, technical: 0.4, fundamentals: 0.0, price: 212 },
  TSLA: { action: "hold", score: -0.04, confidence: 0.07, ml: -0.08, news: 0.25, technical: -0.2, fundamentals: -0.15, price: 342 },
  GOOGL: { action: "hold", score: -0.05, confidence: 0.08, ml: -0.32, news: 0.2, technical: 0.25, fundamentals: 0.2, price: 178 },
  MSFT: { action: "hold", score: -0.06, confidence: 0.09, ml: 0.14, news: 0.15, technical: -0.6, fundamentals: -0.2, price: 477 },
  NVDA: { action: "hold", score: -0.07, confidence: 0.13, ml: -0.02, news: 0.35, technical: -0.4, fundamentals: -0.3, price: 142 },
  DIS: { action: "hold", score: -0.07, confidence: 0.13, ml: -0.01, news: 0.35, technical: -0.6, fundamentals: -0.1, price: 113 },
};

// curated honest theses for a few flagship names (rest are composed)
const THESIS: Record<string, { thesis: string; counter: string[]; conviction: "low" | "medium" | "high" }> = {
  AAPL: {
    thesis:
      "ML and technical signals point to positive near-term momentum, supported by slightly favorable news, but fundamentals offer no clear direction. The moderate score suggests a thin edge — a cautious hold leaning on quantitative signals. Not a high-conviction call; short-term moves can easily surprise.",
    counter: ["ML models may misread changing regimes", "Technical signals can reverse abruptly", "Neutral fundamentals offer no anchor"],
    conviction: "low",
  },
  JNJ: {
    thesis:
      "A buy driven by strong technical momentum (price above its 200-day average) and a constructive ML read, with steady defensive fundamentals. Conviction is moderate — the edge is real but modest, and healthcare names move slowly.",
    counter: ["Slightly soft fundamentals could cap upside", "Defensive names lag in risk-on rallies", "Technical strength may already be priced in"],
    conviction: "medium",
  },
  AMZN: {
    thesis:
      "The strongest ML signal in the universe (+0.56) plus favorable news and healthy fundamentals make this the highest-conviction buy today. Short-term technicals are slightly soft, tempering the call.",
    counter: ["Soft near-term technicals", "Mega-cap crowding risk", "A single in-sample model read"],
    conviction: "high",
  },
};

// --- deterministic price series (seeded random walk) ---
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const BASE_DATE = new Date("2026-06-12T00:00:00Z");

function businessDaysBack(n: number): string[] {
  const out: string[] = [];
  const d = new Date(BASE_DATE);
  while (out.length < n) {
    const dow = d.getUTCDay();
    if (dow !== 0 && dow !== 6) out.unshift(d.toISOString().slice(0, 10));
    d.setUTCDate(d.getUTCDate() - 1);
  }
  return out;
}

function genPrices(seed: number, end: number, n = 160): Bar[] {
  const rnd = mulberry32(seed);
  const dates = businessDaysBack(n);
  const drift = (rnd() - 0.45) * 0.0015;
  const vol = 0.012 + rnd() * 0.012;
  // walk backwards from the known end price
  const closes: number[] = new Array(n);
  closes[n - 1] = end;
  for (let i = n - 2; i >= 0; i--) {
    const r = drift + (rnd() - 0.5) * vol * 2;
    closes[i] = closes[i + 1] / (1 + r);
  }
  return dates.map((time, i) => {
    const c = closes[i];
    const o = i === 0 ? c * (1 - (rnd() - 0.5) * vol) : closes[i - 1];
    const hi = Math.max(o, c) * (1 + rnd() * vol * 0.8);
    const lo = Math.min(o, c) * (1 - rnd() * vol * 0.8);
    return { time, open: +o.toFixed(2), high: +hi.toFixed(2), low: +lo.toFixed(2), close: +c.toFixed(2) };
  });
}

const EVENTS = ["earnings", "product", "analyst", "mna", "macro", "legal", "guidance"];

function genNews(seed: number, name: string, news: number): NewsItem[] {
  const rnd = mulberry32(seed * 7 + 3);
  const dates = businessDaysBack(6);
  const heads = [
    `${name} momentum draws fresh analyst attention`,
    `Hedge funds reposition around ${name} ahead of earnings`,
    `${name} unveils strategy update; investor reaction mixed`,
    `Options activity in ${name} picks up this week`,
    `${name} navigates shifting demand backdrop`,
  ];
  return heads.slice(0, 4).map((title, i) => ({
    date: dates[dates.length - 1 - i],
    title,
    score: +(news * (0.6 + rnd() * 0.6) + (rnd() - 0.5) * 0.3).toFixed(2),
    confidence: +(0.2 + rnd() * 0.5).toFixed(2),
    event_type: EVENTS[Math.floor(rnd() * EVENTS.length)],
  }));
}

function genFundamentals(seed: number, fundamentals: number): FundamentalRow[] {
  const rnd = mulberry32(seed * 13 + 5);
  const periods = ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"];
  const base = 20_000_000_000 * (0.4 + rnd() * 2);
  const rows: FundamentalRow[] = [];
  for (const metric of ["revenue", "net_income", "eps_diluted"] as const) {
    let prev = 0;
    periods.forEach((p, i) => {
      const trend = 1 + fundamentals * 0.12 + (rnd() - 0.5) * 0.08;
      const v =
        metric === "eps_diluted"
          ? +(1 + rnd() * 2.4).toFixed(2)
          : Math.round((metric === "net_income" ? base * 0.24 : base) * Math.pow(trend, i));
      rows.push({
        metric,
        period_end: p,
        value: v,
        yoy: i >= 1 && prev ? (v - prev) / Math.abs(prev) : null,
        isEps: metric === "eps_diluted",
      });
      if (i === 0) prev = v;
      else prev = rows[rows.length - 5]?.value ?? v;
    });
  }
  return rows;
}

const WORD = (v: number, up: string, down: string, flat: string) =>
  v > 0.15 ? up : v < -0.15 ? down : flat;

function buildSignals(name: string, r: Raw, seed: number): AgentSignal[] {
  const rnd = mulberry32(seed * 17 + 9);
  return [
    {
      agent: "news",
      signal: r.news,
      confidence: +(0.3 + Math.abs(r.news) * 0.5).toFixed(2),
      summary: `Recent coverage of ${name} reads ${WORD(r.news, "constructive", "cautious", "mixed")}; flow is dominated by ${r.news > 0 ? "positive product and analyst items" : "macro and rotation noise"}.`,
      key_events: [
        `${name} ${r.news > 0 ? "gains favorable analyst commentary" : "faces sector rotation pressure"}`,
        `Positioning shifts noted around ${name}`,
      ],
      catalysts: ["Upcoming earnings date", "Product / demand data points"],
    },
    {
      agent: "technical",
      signal: r.technical,
      confidence: +(0.3 + Math.abs(r.technical) * 0.4).toFixed(2),
      regime: WORD(r.technical, "uptrend", "downtrend", "range"),
      rationale: `Trend read is ${WORD(r.technical, "bullish — price above key moving averages with positive momentum", "bearish — price below moving averages, momentum rolling over", "neutral — range-bound with mixed momentum")}. ${rnd() > 0.5 ? "RSI is mid-range." : "Volatility is contained."}`,
    },
    {
      agent: "fundamentals",
      signal: r.fundamentals,
      confidence: +(0.3 + Math.abs(r.fundamentals) * 0.5).toFixed(2),
      valuation_view: WORD(r.fundamentals, "cheap", "expensive", "fair"),
      growth_view: WORD(r.fundamentals, "accelerating", "decelerating", "steady"),
      red_flags: r.fundamentals < -0.1 ? ["Margin pressure to watch"] : [],
      rationale: `Quarterly trajectory looks ${WORD(r.fundamentals, "supportive with steady YoY growth", "soft, with growth decelerating", "broadly stable")}.`,
    },
  ];
}

function composeThesis(name: string, r: Raw) {
  if (THESIS[tickerByName(name)]) return THESIS[tickerByName(name)];
  const legs: string[] = [];
  if (Math.abs(r.ml) > 0.15) legs.push(`the ML model leans ${r.ml > 0 ? "bullish" : "bearish"}`);
  if (Math.abs(r.technical) > 0.2) legs.push(`technicals are ${r.technical > 0 ? "constructive" : "weak"}`);
  if (Math.abs(r.news) > 0.2) legs.push(`news flow is ${r.news > 0 ? "favorable" : "soft"}`);
  const head = r.action === "buy" ? "A cautious buy" : r.action === "sell" ? "A lean to reduce" : "No clear edge";
  return {
    thesis: `${head} on ${name}: ${legs.join(", ") || "signals are close to neutral"}. The combined score is modest, so treat this as decision support, not a high-conviction call — markets are hard to predict over a week.`,
    counter: [
      r.fundamentals < 0 ? "Fundamentals provide no supportive anchor" : "Conviction is thin",
      "Signals can reverse on a single macro print",
      "One in-sample model read",
    ],
    conviction: (r.confidence > 0.5 ? "medium" : "low") as "low" | "medium",
  };
}

function tickerByName(name: string): string {
  return UNIVERSE.find((s) => s.name === name)?.ticker ?? "";
}

function buildTicker(stock: Stock, idx: number): TickerData {
  const r = RAW[stock.ticker];
  const prices = genPrices(idx + 1, r.price);
  const last = prices[prices.length - 1];
  const prev = prices[prices.length - 2];
  const t = composeThesis(stock.name, r);
  const rec: Recommendation = {
    ticker: stock.ticker,
    asOf: "2026-06-11",
    action: r.action,
    score: r.score,
    confidence: r.confidence,
    mlProba: +(0.5 + r.ml / 2).toFixed(2),
    components: { ml: r.ml, news: r.news, technical: r.technical, fundamentals: r.fundamentals },
    riskLevel: r.confidence > 0.5 ? "low" : r.confidence > 0.2 ? "moderate" : "high",
    maxPositionPct: +(3 + r.confidence * 6).toFixed(0),
    stopLossPct: r.action === "hold" ? null : +(5 + (1 - r.confidence) * 6).toFixed(0),
    riskFlags:
      r.technical > 0.5 ? ["near short-term overbought"] : r.fundamentals < -0.2 ? ["weak fundamentals"] : [],
    thesis: t.thesis,
    counterarguments: t.counter,
    conviction: t.conviction,
  };
  return {
    stock,
    rec,
    signals: buildSignals(stock.name, r, idx + 1),
    prices,
    news: genNews(idx + 1, stock.name, r.news),
    fundamentals: genFundamentals(idx + 1, r.fundamentals),
    lastClose: last.close,
    change1d: (last.close - prev.close) / prev.close,
  };
}

export const TICKERS: Record<string, TickerData> = Object.fromEntries(
  UNIVERSE.map((s, i) => [s.ticker, buildTicker(s, i)]),
);

export const ALL: TickerData[] = UNIVERSE.map((s) => TICKERS[s.ticker]);

export const COST = { today: 0.0687, total: 0.214, calls: 312 };
