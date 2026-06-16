import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type Action = "buy" | "hold" | "sell";

export const actionColor: Record<Action, string> = {
  buy: "text-buy",
  sell: "text-sell",
  hold: "text-hold",
};

export const actionBg: Record<Action, string> = {
  buy: "bg-buy/12 text-buy border-buy/30",
  sell: "bg-sell/12 text-sell border-sell/30",
  hold: "bg-hold/12 text-hold border-hold/25",
};

/** Map a signal in [-1, 1] to a semantic color string (rgb). */
export function signalRGB(v: number): string {
  if (v >= 0.12) return "var(--buy)";
  if (v <= -0.12) return "var(--sell)";
  return "var(--hold)";
}

export function fmtSigned(v: number, digits = 2): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}`;
}

export function fmtPct(v: number, digits = 1): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(digits)}%`;
}

export function fmtCompact(v: number): string {
  if (Math.abs(v) >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
  if (Math.abs(v) >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
  return v.toFixed(2);
}
