"use client";

import { TriangleAlert } from "lucide-react";
import type { Recommendation } from "@/lib/types";
import {
  actionBg,
  actionBorder,
  actionColor,
  actionWash,
  convictionColor,
  riskColor,
} from "@/lib/colors";
import { ConfidenceRing } from "@/components/fx/ConfidenceRing";
import { CountUp } from "@/components/fx/CountUp";

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-faint">{label}</div>
      <div className="text-sm font-semibold">{children}</div>
    </div>
  );
}

export function RecHero({ rec }: { rec: Recommendation }) {
  const ac = actionColor(rec.action);
  return (
    <div
      className="rounded-[18px] border p-[22px] shadow-[0_22px_55px_-42px_rgba(0,0,0,0.9)]"
      style={{
        borderColor: actionBorder(rec.action),
        background: `linear-gradient(180deg,${actionWash(rec.action)},rgba(16,19,27,0.65))`,
      }}
    >
      <div className="mb-[18px] flex items-center justify-between gap-3">
        <span className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-faint">
          Recommendation
        </span>
        <span className="inline-flex items-center gap-1.5 text-[0.7rem] text-muted">
          <span className="h-[5px] w-[5px] rounded-full bg-faint" />
          Not advice
        </span>
      </div>

      <div className="flex items-center gap-[18px]">
        <ConfidenceRing value={rec.confidence} color={ac} />
        <div className="min-w-0">
          <div
            className="inline-flex items-center gap-2 rounded-[11px] border px-3.5 py-1.5"
            style={{ background: actionBg(rec.action), borderColor: actionBorder(rec.action) }}
          >
            <span
              className="h-[9px] w-[9px] rounded-full"
              style={{ background: ac, boxShadow: `0 0 12px ${ac}` }}
            />
            <span className="text-[1.35rem] font-extrabold tracking-[0.01em]" style={{ color: ac }}>
              {rec.action.toUpperCase()}
            </span>
          </div>
          <div className="mt-4 flex gap-[18px]">
            <Stat label="Conviction">
              <span style={{ color: convictionColor(rec.conviction) }}>{cap(rec.conviction)}</span>
            </Stat>
            <Stat label="Score">
              <CountUp value={rec.score} decimals={2} signed className="font-mono" />
            </Stat>
            <Stat label="ML prob">
              <CountUp value={Math.round(rec.mlProba * 100)} suffix="%" className="font-mono" />
            </Stat>
          </div>
        </div>
      </div>

      {/* risk sizing */}
      <div className="mt-5 border-t border-line-2 pt-[18px]">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[0.62rem] font-semibold uppercase tracking-[0.13em] text-faint">
            Risk sizing
          </span>
          <span
            className="inline-flex items-center gap-1.5 text-xs font-semibold"
            style={{ color: riskColor(rec.riskLevel) }}
          >
            <span className="h-[7px] w-[7px] rounded-full" style={{ background: riskColor(rec.riskLevel) }} />
            {cap(rec.riskLevel)} risk
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-[11px] border border-line-2 bg-ink/40 px-3 py-2.5">
            <div className="mb-1 text-[0.6rem] font-semibold uppercase tracking-[0.08em] text-faint">
              Max position
            </div>
            <CountUp
              value={rec.maxPositionPct}
              suffix="%"
              className="font-mono text-lg font-semibold"
            />
          </div>
          <div className="rounded-[11px] border border-line-2 bg-ink/40 px-3 py-2.5">
            <div className="mb-1 text-[0.6rem] font-semibold uppercase tracking-[0.08em] text-faint">
              Stop loss
            </div>
            <div className="font-mono text-lg font-semibold">
              {rec.stopLossPct != null ? `${rec.stopLossPct}%` : "—"}
            </div>
          </div>
        </div>
        {rec.riskFlags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {rec.riskFlags.map((flag) => (
              <span
                key={flag}
                className="inline-flex items-center gap-1.5 rounded-[7px] border px-2.5 py-1 text-[0.72rem] font-medium"
                style={{
                  color: "#e7b9bd",
                  background: "rgba(244,100,110,0.09)",
                  borderColor: "rgba(244,100,110,0.22)",
                }}
              >
                <TriangleAlert size={11} />
                {flag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
