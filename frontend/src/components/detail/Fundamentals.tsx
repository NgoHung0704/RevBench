import type { FundamentalRow } from "@/lib/types";
import { fmtCompact } from "@/lib/utils";
import { fmtPctU, numColor } from "@/lib/colors";

function value(f: FundamentalRow): string {
  if (f.isEps) return `$${f.value.toFixed(2)}`;
  return Math.abs(f.value) >= 1000 ? `$${fmtCompact(f.value)}` : fmtCompact(f.value);
}

export function Fundamentals({ rows }: { rows: FundamentalRow[] }) {
  const period = rows[0]?.period_end ?? "—";
  return (
    <div className="rounded-2xl border border-line bg-surface/60 px-5 py-[18px] shadow-[0_22px_50px_-42px_rgba(0,0,0,0.85)]">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-[0.94rem] font-bold">Fundamentals</h2>
        <span className="font-mono text-[0.72rem] text-faint">FQ {period}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto_auto]">
        <div className="py-1.5 text-[0.6rem] font-semibold uppercase tracking-[0.1em] text-faint-2">Metric</div>
        <div className="py-1.5 pr-4 text-right text-[0.6rem] font-semibold uppercase tracking-[0.1em] text-faint-2">
          Value
        </div>
        <div className="min-w-[62px] py-1.5 text-right text-[0.6rem] font-semibold uppercase tracking-[0.1em] text-faint-2">
          YoY
        </div>
        {rows.map((f, i) => (
          <div key={i} className="contents">
            <div className="border-t border-line-2 py-2.5 text-[0.81rem] text-[#cdd3df]">{f.metric}</div>
            <div className="border-t border-line-2 py-2.5 pr-4 text-right font-mono text-[0.81rem] text-text">
              {value(f)}
            </div>
            <div
              className="border-t border-line-2 py-2.5 text-right font-mono text-[0.78rem]"
              style={{ color: f.yoy != null ? numColor(f.yoy) : "rgb(var(--faint))" }}
            >
              {f.yoy != null ? fmtPctU(f.yoy) : "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
