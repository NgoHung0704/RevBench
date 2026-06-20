"use client";

import { useMemo, useState } from "react";
import type { TickerSummary } from "@/lib/types";
import type { Action } from "@/lib/utils";
import { Reveal } from "@/components/fx/Reveal";
import { TickerCard } from "@/components/TickerCard";
import { AgentMatrix } from "@/components/AgentMatrix";

type ActionFilter = "all" | Action;
type ConvFilter = "all" | "high" | "medium" | "low";
type SortKey = "confidence" | "score" | "change" | "ticker";

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { key: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex gap-1 rounded-xl border border-line bg-surface/50 p-1">
      {options.map((o) => {
        const active = o.key === value;
        return (
          <button
            key={o.key}
            onClick={() => onChange(o.key)}
            className="seg"
            style={{
              color: active ? "#0d0f14" : "rgb(var(--muted))",
              background: active ? "#d6b27a" : "transparent",
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function ConvictionBoard({ universe }: { universe: TickerSummary[] }) {
  const [action, setAction] = useState<ActionFilter>("all");
  const [conv, setConv] = useState<ConvFilter>("all");
  const [sortBy, setSortBy] = useState<SortKey>("confidence");

  const list = useMemo(() => {
    const filtered = universe
      .filter((d) => action === "all" || d.rec.action === action)
      .filter((d) => conv === "all" || d.rec.conviction === conv);
    return [...filtered].sort((a, b) => {
      if (sortBy === "confidence") return b.rec.confidence - a.rec.confidence;
      if (sortBy === "score") return b.rec.score - a.rec.score;
      if (sortBy === "change") return b.change1d - a.change1d;
      return a.stock.ticker < b.stock.ticker ? -1 : 1;
    });
  }, [universe, action, conv, sortBy]);

  const signature = `${action}-${conv}-${sortBy}`;

  return (
    <div className="mx-auto max-w-content px-5 pb-10 pt-8 sm:px-7">
      {/* page head */}
      <div className="mb-5 flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="text-[1.7rem] font-extrabold tracking-tight text-text">Conviction Board</h1>
          <p className="mt-1.5 max-w-[46ch] text-sm leading-relaxed text-muted">
            One AI recommendation per ticker across {universe.length} blue-chip names — with
            confidence, risk sizing, and an honest thesis.
          </p>
        </div>
        <div className="rounded-xl border border-line bg-surface/60 px-4 py-3">
          <div className="label mb-1">Strategy vs Buy &amp; Hold</div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-lg font-semibold text-sell">Sharpe 0.45</span>
            <span className="text-[0.72rem] text-muted">vs 1.17 — model trails (backtest)</span>
          </div>
        </div>
      </div>

      {/* controls */}
      <div className="mb-5 flex flex-wrap items-center gap-3.5">
        <Segmented<ActionFilter>
          options={[
            { key: "all", label: "All" },
            { key: "buy", label: "Buy" },
            { key: "hold", label: "Hold" },
            { key: "sell", label: "Sell" },
          ]}
          value={action}
          onChange={setAction}
        />
        <div className="flex items-center gap-2">
          <span className="label">Conviction</span>
          <Segmented<ConvFilter>
            options={[
              { key: "all", label: "All" },
              { key: "high", label: "High" },
              { key: "medium", label: "Medium" },
              { key: "low", label: "Low" },
            ]}
            value={conv}
            onChange={setConv}
          />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="label">Sort</span>
          <Segmented<SortKey>
            options={[
              { key: "confidence", label: "Confidence" },
              { key: "score", label: "Score" },
              { key: "change", label: "Change" },
              { key: "ticker", label: "A–Z" },
            ]}
            value={sortBy}
            onChange={setSortBy}
          />
        </div>
      </div>

      {/* card grid (re-keyed so filter/sort replays the staggered entrance) */}
      {list.length > 0 ? (
        <div
          key={signature}
          className="mb-8 grid gap-4"
          style={{ gridTemplateColumns: "repeat(auto-fill, minmax(282px, 1fr))" }}
        >
          {list.map((d, i) => (
            <TickerCard key={d.stock.ticker} d={d} index={i} />
          ))}
        </div>
      ) : (
        <div className="mb-8 rounded-2xl border border-dashed border-line-2 px-6 py-12 text-center text-sm text-faint">
          No tickers match these filters.
        </div>
      )}

      <Reveal>
        <AgentMatrix universe={universe} />
      </Reveal>
    </div>
  );
}
