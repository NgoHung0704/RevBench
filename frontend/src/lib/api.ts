import type { CostSummary, TickerData, TickerSummary } from "./types";

// The FastAPI backend (backend/app) serves shapes identical to types.ts.
// Set NEXT_PUBLIC_API_URL to point at a deployed API; defaults to local dev.
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // backend not running — pages render a friendly empty state
    return null;
  }
}

export const getUniverse = () => get<TickerSummary[]>("/api/universe");
export const getTicker = (symbol: string) => get<TickerData>(`/api/tickers/${symbol}`);
export const getCost = () => get<CostSummary>("/api/cost");

export const API_BASE = BASE;
