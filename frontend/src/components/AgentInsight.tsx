import { Newspaper, LineChart, Building2 } from "lucide-react";
import type { AgentSignal } from "@/lib/types";
import { fmtSigned, signalRGB } from "@/lib/utils";

const ICON = { news: Newspaper, technical: LineChart, fundamentals: Building2 };

export function AgentInsight({ s }: { s: AgentSignal }) {
  const Icon = ICON[s.agent];
  const color = signalRGB(s.signal);
  return (
    <div className="card animate-fade-up p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg border border-line/70 bg-surface-2/60 text-muted">
            <Icon size={16} />
          </span>
          <div>
            <p className="font-medium capitalize text-text">{s.agent}</p>
            <p className="label mt-0.5">deepseek-v4-pro</p>
          </div>
        </div>
        <div className="text-right">
          <p className="tnum text-xl font-medium" style={{ color: `rgb(${color})` }}>
            {fmtSigned(s.signal)}
          </p>
          <p className="label">conf {s.confidence.toFixed(2)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {s.regime && <span className="chip capitalize">{s.regime}</span>}
        {s.valuation_view && <span className="chip capitalize">valuation: {s.valuation_view}</span>}
        {s.growth_view && <span className="chip capitalize">growth: {s.growth_view}</span>}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-muted">{s.rationale ?? s.summary}</p>

      {s.key_events && s.key_events.length > 0 && (
        <List title="Key events" items={s.key_events} />
      )}
      {s.catalysts && s.catalysts.length > 0 && <List title="Catalysts" items={s.catalysts} />}
      {s.red_flags && s.red_flags.length > 0 && (
        <List title="Red flags" items={s.red_flags} tone="sell" />
      )}
    </div>
  );
}

function List({ title, items, tone }: { title: string; items: string[]; tone?: "sell" }) {
  return (
    <div className="mt-3">
      <p className={`label mb-1.5 ${tone === "sell" ? "text-sell/80" : ""}`}>{title}</p>
      <ul className="space-y-1">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2 text-sm text-muted">
            <span className={tone === "sell" ? "text-sell/60" : "text-gold/60"}>—</span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
