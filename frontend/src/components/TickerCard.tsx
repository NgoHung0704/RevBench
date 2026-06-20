"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { TickerSummary } from "@/lib/types";
import { DUR, EASE } from "@/lib/motion";
import {
  actionBg,
  actionBorder,
  actionColor,
  convictionColor,
  fmtMoney,
  fmtPctU,
  numColor,
} from "@/lib/colors";
import { GrowBar } from "@/components/fx/Bars";
import { Sparkline } from "@/components/Sparkline";

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function TickerCard({ d, index = 0 }: { d: TickerSummary; index?: number }) {
  const { stock, rec } = d;
  const up = d.change1d >= 0;
  const delay = Math.min(index * 0.032, 0.34);
  const conf = Math.round(rec.confidence * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.36, ease: EASE, delay }}
    >
      <Link
        href={`/ticker/${stock.ticker}`}
        aria-label={`${stock.ticker} ${stock.name}, ${rec.action}, confidence ${conf} percent`}
        className="group block rounded-2xl border border-line bg-gradient-to-b from-surface-2/60 to-surface/60 p-4 shadow-[0_1px_0_0_rgba(255,255,255,0.02)_inset,0_22px_50px_-38px_rgba(0,0,0,0.85)] backdrop-blur-sm transition duration-150 hover:-translate-y-0.5 hover:border-[#33405a] hover:shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_26px_46px_-30px_rgba(0,0,0,0.9),0_0_0_1px_rgba(214,178,122,0.12)]"
      >
        <div className="flex items-start justify-between gap-2.5">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-base font-semibold tracking-[0.02em] text-text">
                {stock.ticker}
              </span>
              <span className="whitespace-nowrap rounded-[5px] border border-line px-1.5 py-px text-[0.6rem] font-semibold tracking-wide text-faint">
                {stock.sector}
              </span>
            </div>
            <div className="mt-0.5 max-w-[150px] truncate text-[0.78rem] text-muted">{stock.name}</div>
          </div>
          <span
            className="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[0.72rem] font-bold tracking-[0.04em]"
            style={{ color: actionColor(rec.action), background: actionBg(rec.action), borderColor: actionBorder(rec.action) }}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: actionColor(rec.action) }} />
            {rec.action.toUpperCase()}
          </span>
        </div>

        <div className="my-3 h-[42px]">
          <Sparkline
            bars={d.prices}
            color={up ? "rgba(56,201,138,0.85)" : "rgba(244,100,110,0.85)"}
            delay={delay + 0.1}
          />
        </div>

        <div className="flex items-end justify-between gap-2.5">
          <div>
            <div className="font-mono text-[1.05rem] font-semibold text-text">{fmtMoney(d.lastClose)}</div>
            <div className="mt-0.5 font-mono text-xs font-medium" style={{ color: numColor(d.change1d) }}>
              {fmtPctU(d.change1d)}
            </div>
          </div>
          <div className="flex-none text-right">
            <div className="mb-1.5 whitespace-nowrap text-[0.62rem] font-semibold uppercase tracking-[0.08em]">
              <span style={{ color: convictionColor(rec.conviction) }}>{cap(rec.conviction)}</span>
              <span className="text-faint"> · conf</span>
            </div>
            <div className="flex items-center justify-end gap-2">
              <GrowBar
                value={rec.confidence}
                color={convictionColor(rec.conviction)}
                delay={delay + 0.12}
                trackClass="h-[5px] w-[62px] bg-line-2"
              />
              <span className="min-w-[30px] text-right font-mono text-xs text-[#cdd3df]">{conf}%</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
