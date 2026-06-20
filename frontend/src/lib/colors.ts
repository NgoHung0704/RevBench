// Color maps + small formatting helpers shared across the redesigned UI.
// Hex values mirror docs/DESIGN_BRIEF.md §1 (semantic number tints are slightly
// lighter than the base buy/sell so figures stay AA on dark surfaces).
import type { Action } from "./utils";

export const ACTION: Record<Action, string> = { buy: "#38c98a", sell: "#f4646e", hold: "#818c9f" };
export const CONVICTION: Record<string, string> = { high: "#38c98a", medium: "#d6b27a", low: "#97a0b1" };
export const RISK: Record<string, string> = { low: "#38c98a", moderate: "#d6b27a", high: "#f4646e" };
export const GOLD = "#d6b27a";
export const INFO = "#6f86c9";
export const NUM_UP = "#5fcfa0";
export const NUM_DOWN = "#ef8b94";

export const actionColor = (a: Action) => ACTION[a];
export const actionBg = (a: Action) =>
  a === "buy" ? "rgba(56,201,138,0.10)" : a === "sell" ? "rgba(244,100,110,0.10)" : "rgba(129,140,159,0.10)";
export const actionBorder = (a: Action) =>
  a === "buy" ? "rgba(56,201,138,0.30)" : a === "sell" ? "rgba(244,100,110,0.30)" : "rgba(129,140,159,0.28)";
export const actionWash = (a: Action) =>
  a === "buy" ? "rgba(56,201,138,0.06)" : a === "sell" ? "rgba(244,100,110,0.06)" : "rgba(129,140,159,0.05)";

export const convictionColor = (c: string) => CONVICTION[c] ?? CONVICTION.low;
export const riskColor = (r: string) => RISK[r] ?? CONVICTION.low;

/** Number tint by sign (lighter than base buy/sell for AA on dark). */
export const numColor = (v: number) => (v >= 0 ? NUM_UP : NUM_DOWN);

/** Map a signed component contribution to an agent signal in [-1, 1]. */
export const agentSig = (comp: number) => Math.max(-1, Math.min(1, comp * 3.1));

const MINUS = "−"; // unicode minus

export const fmtMoney = (v: number) =>
  "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Signed, unicode-minus, fixed decimals. For a percentage pass a value already
 *  in percent units (e.g. 1.47 → "+1.47%"); use `pct` for fractions. */
export const fmtSignedU = (v: number, decimals = 2, suffix = "") =>
  (v >= 0 ? "+" : MINUS) + Math.abs(v).toFixed(decimals) + suffix;

/** Signed percent from a fraction (0.0147 → "+1.47%"). */
export const fmtPctU = (frac: number, decimals = 2) => fmtSignedU(frac * 100, decimals, "%");
