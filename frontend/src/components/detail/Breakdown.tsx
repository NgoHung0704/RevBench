"use client";

import type { Recommendation } from "@/lib/types";
import { fmtSignedU, numColor } from "@/lib/colors";
import { BipolarBar } from "@/components/fx/Bars";

const ORDER: { key: keyof Recommendation["components"]; label: string }[] = [
  { key: "ml", label: "ML model" },
  { key: "news", label: "News" },
  { key: "technical", label: "Technical" },
  { key: "fundamentals", label: "Fundamentals" },
];

export function Breakdown({ components }: { components: Recommendation["components"] }) {
  const maxAbs = Math.max(...ORDER.map((o) => Math.abs(components[o.key])), 0.0001);
  return (
    <div className="rounded-2xl border border-line bg-surface/60 px-[22px] py-5 shadow-[0_22px_50px_-42px_rgba(0,0,0,0.85)]">
      <div className="mb-[18px] flex items-center justify-between">
        <div>
          <h2 className="mb-0.5 text-[0.94rem] font-bold">Signal contribution</h2>
          <p className="text-[0.78rem] text-muted">Signed push toward the recommendation, by source.</p>
        </div>
        <span className="text-[0.7rem] text-faint">← sell · buy →</span>
      </div>
      <div className="flex flex-col gap-3.5">
        {ORDER.map((o, i) => {
          const v = components[o.key];
          return (
            <div key={o.key} className="grid grid-cols-[108px_1fr_56px] items-center gap-3.5">
              <span className="text-[0.81rem] font-semibold text-[#cdd3df]">{o.label}</span>
              <BipolarBar
                value={v}
                max={maxAbs}
                posColor="#38c98a"
                negColor="#f4646e"
                delay={0.2 + i * 0.06}
              />
              <span
                className="text-right font-mono text-[0.78rem] font-medium"
                style={{ color: numColor(v) }}
              >
                {fmtSignedU(v, 2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
