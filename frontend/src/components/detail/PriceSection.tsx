"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";
import type { Bar } from "@/lib/types";
import { fmtMoney } from "@/lib/colors";
import { PriceChart } from "@/components/PriceChart";

const RANGES: { key: string; label: string; days: number; full: string }[] = [
  { key: "1M", label: "1M", days: 22, full: "1 month" },
  { key: "3M", label: "3M", days: 66, full: "3 months" },
  { key: "6M", label: "6M", days: 132, full: "6 months" },
  { key: "1Y", label: "1Y", days: 260, full: "1 year" },
];

export function PriceSection({ bars, ticker, lastClose }: { bars: Bar[]; ticker: string; lastClose: number }) {
  const reduce = useReducedMotion();
  const [range, setRange] = useState("6M");
  const cfg = RANGES.find((r) => r.key === range)!;
  const sliced = bars.slice(-cfg.days);
  const aria = `${ticker} daily candlestick chart over ${cfg.full}, last close ${fmtMoney(lastClose)}`;

  return (
    <div className="rounded-2xl border border-line bg-surface/60 px-5 pb-3.5 pt-[18px] shadow-[0_22px_50px_-42px_rgba(0,0,0,0.85)]">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-3.5">
        <div className="flex items-baseline gap-3">
          <h2 className="text-[0.94rem] font-bold">Price</h2>
          <span className="text-xs text-faint">{cfg.full} · daily candles</span>
        </div>
        <div className="flex gap-1 rounded-[10px] border border-line bg-ink/50 p-1">
          {RANGES.map((r) => {
            const active = r.key === range;
            return (
              <button
                key={r.key}
                onClick={() => setRange(r.key)}
                aria-label={`Show ${r.key} range`}
                className="cursor-pointer rounded-[7px] border-none px-2.5 py-1 font-mono text-xs font-medium transition"
                style={{ color: active ? "#0d0f14" : "rgb(var(--muted))", background: active ? "#d6b27a" : "transparent" }}
              >
                {r.label}
              </button>
            );
          })}
        </div>
      </div>
      <motion.div
        role="img"
        aria-label={aria}
        initial={reduce ? false : { clipPath: "inset(0 100% 0 0)" }}
        animate={{ clipPath: "inset(0 0% 0 0)" }}
        transition={{ duration: DUR.draw, ease: EASE, delay: 0.2 }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={range}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: EASE }}
          >
            <PriceChart bars={sliced} />
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
