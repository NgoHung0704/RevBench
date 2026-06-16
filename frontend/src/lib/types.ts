import type { Action } from "./utils";

// Shapes mirror the read layer in ui/data.py + agents/schemas.py so swapping mock
// data for the real FastAPI backend (Phase 6) is a one-file change.

export interface Stock {
  ticker: string;
  name: string;
  sector: string;
}

export interface Bar {
  time: string; // YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;
}

export type AgentName = "news" | "technical" | "fundamentals";

export interface AgentSignal {
  agent: AgentName;
  signal: number; // [-1, 1]
  confidence: number; // [0, 1]
  // a readable subset of the agent's structured payload
  regime?: string;
  valuation_view?: string;
  growth_view?: string;
  rationale?: string;
  summary?: string;
  key_events?: string[];
  catalysts?: string[];
  red_flags?: string[];
}

export interface NewsItem {
  date: string;
  title: string;
  score: number;
  confidence: number;
  event_type: string;
}

export interface FundamentalRow {
  metric: string;
  period_end: string;
  value: number;
  yoy: number | null;
  isEps?: boolean;
}

export interface Recommendation {
  ticker: string;
  asOf: string;
  action: Action;
  score: number;
  confidence: number;
  mlProba: number;
  components: { ml: number; news: number; technical: number; fundamentals: number };
  // advisory enrichment (Risk + Strategist)
  riskLevel: "low" | "moderate" | "high";
  maxPositionPct: number;
  stopLossPct: number | null;
  riskFlags: string[];
  thesis: string;
  counterarguments: string[];
  conviction: "low" | "medium" | "high";
}

export interface TickerData {
  stock: Stock;
  rec: Recommendation;
  signals: AgentSignal[];
  prices: Bar[];
  news: NewsItem[];
  fundamentals: FundamentalRow[];
  lastClose: number;
  change1d: number;
}
