"use client";

import Link from "next/link";
import { agentSig, fmtSignedU } from "@/lib/colors";
import type { TickerSummary } from "@/lib/types";

const COLS: { key: "news" | "technical" | "fundamentals"; label: string }[] = [
  { key: "news", label: "News" },
  { key: "technical", label: "Technical" },
  { key: "fundamentals", label: "Fundamentals" },
];

function cell(comp: number) {
  const s = agentSig(comp);
  const m = Math.min(Math.abs(s), 1);
  const a = (0.08 + 0.42 * m).toFixed(2);
  const bg =
    s > 0.02 ? `rgba(56,201,138,${a})` : s < -0.02 ? `rgba(244,100,110,${a})` : "rgba(129,140,159,0.10)";
  const border =
    s > 0.02 ? "rgba(56,201,138,0.22)" : s < -0.02 ? "rgba(244,100,110,0.22)" : "rgb(var(--line-2))";
  const text = m > 0.4 ? "#eef1f6" : "#cdd3df";
  return { val: fmtSignedU(s, 2), bg, border, text };
}

export function AgentMatrix({ universe }: { universe: TickerSummary[] }) {
  return (
    <div className="card px-5 pb-2 pt-5">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-base font-bold tracking-tight text-text">Agent Signal Matrix</h2>
          <p className="mt-1 text-[0.78rem] text-muted">
            Signed conviction per reasoning agent. Hover a cell for the value.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <span className="text-[0.7rem] text-faint">Sell</span>
          <div
            className="h-2 w-[120px] rounded-full"
            style={{ background: "linear-gradient(90deg,#f4646e,#2a3040 48%,#2a3040 52%,#38c98a)" }}
          />
          <span className="text-[0.7rem] text-faint">Buy</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div className="min-w-[560px]">
          <div className="mb-1.5 grid grid-cols-[160px_repeat(3,1fr)] gap-1.5">
            <div />
            {COLS.map((c) => (
              <div
                key={c.key}
                className="text-center text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-faint"
              >
                {c.label}
              </div>
            ))}
          </div>
          {universe.map((d) => (
            <Link
              key={d.stock.ticker}
              href={`/ticker/${d.stock.ticker}`}
              className="mb-1.5 grid grid-cols-[160px_repeat(3,1fr)] gap-1.5"
            >
              <div className="flex items-center gap-2 pr-2">
                <span className="font-mono text-[0.82rem] font-semibold text-text">{d.stock.ticker}</span>
                <span className="truncate text-[0.72rem] text-faint">{d.stock.name}</span>
              </div>
              {COLS.map((c) => {
                const cl = cell(d.rec.components[c.key]);
                return (
                  <div
                    key={c.key}
                    title={`${d.stock.ticker} ${c.key}: ${cl.val}`}
                    className="flex h-[34px] items-center justify-center rounded-lg border transition duration-150 hover:-translate-y-px"
                    style={{ background: cl.bg, borderColor: cl.border }}
                  >
                    <span className="font-mono text-xs font-medium" style={{ color: cl.text }}>
                      {cl.val}
                    </span>
                  </div>
                );
              })}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
