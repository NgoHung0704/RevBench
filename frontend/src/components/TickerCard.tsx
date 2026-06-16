import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { TickerData } from "@/lib/types";
import { fmtPct, fmtSigned, signalRGB } from "@/lib/utils";
import { ActionBadge } from "./Badge";
import { ScoreMeter } from "./Meters";
import { Sparkline } from "./Sparkline";

export function TickerCard({ d }: { d: TickerData }) {
  const up = d.change1d >= 0;
  const legs: [string, number][] = [
    ["ML", d.rec.components.ml],
    ["News", d.rec.components.news],
    ["Tech", d.rec.components.technical],
    ["Fund", d.rec.components.fundamentals],
  ];
  return (
    <Link
      href={`/ticker/${d.stock.ticker}`}
      className="card group relative block p-5 transition duration-300 hover:-translate-y-0.5 hover:border-gold/30"
    >
      <ArrowUpRight
        size={16}
        className="absolute right-4 top-4 text-faint opacity-0 transition group-hover:opacity-100"
      />
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-lg font-semibold tracking-tight text-text">{d.stock.ticker}</p>
          <p className="text-sm text-muted">{d.stock.name}</p>
        </div>
        <ActionBadge action={d.rec.action} />
      </div>

      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="tnum text-2xl text-text">${d.lastClose.toFixed(2)}</p>
          <p className="tnum text-sm" style={{ color: up ? "rgb(var(--buy))" : "rgb(var(--sell))" }}>
            {fmtPct(d.change1d)}
          </p>
        </div>
        <Sparkline bars={d.prices} up={up} />
      </div>

      <div className="mt-4">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="label">Combined score</span>
          <span className="tnum text-sm font-medium" style={{ color: `rgb(${signalRGB(d.rec.score)})` }}>
            {fmtSigned(d.rec.score)}
          </span>
        </div>
        <ScoreMeter value={d.rec.score} />
      </div>

      <div className="mt-4 grid grid-cols-4 gap-2 border-t border-line/50 pt-3">
        {legs.map(([k, v]) => (
          <div key={k}>
            <p className="label">{k}</p>
            <p className="tnum text-sm" style={{ color: `rgb(${signalRGB(v)})` }}>
              {fmtSigned(v)}
            </p>
          </div>
        ))}
      </div>
    </Link>
  );
}
