import { cn, fmtSigned, signalRGB } from "@/lib/utils";

/** Bipolar bar for a value in [-1, 1] with a centered zero. */
export function ScoreMeter({ value, className }: { value: number; className?: string }) {
  const pct = Math.max(-1, Math.min(1, value)) * 50;
  const color = signalRGB(value);
  return (
    <div className={cn("relative h-2 w-full rounded-full bg-surface-2", className)}>
      <div className="absolute left-1/2 top-0 h-full w-px bg-line" />
      <div
        className="absolute top-0 h-full rounded-full transition-all"
        style={{
          background: `rgb(${color})`,
          left: pct >= 0 ? "50%" : `${50 + pct}%`,
          width: `${Math.abs(pct)}%`,
          boxShadow: `0 0 12px rgb(${color} / 0.5)`,
        }}
      />
    </div>
  );
}

/** Compact bipolar bar used inside the agent heatmap cells. */
export function SignalBar({ value }: { value: number }) {
  const pct = Math.max(-1, Math.min(1, value)) * 50;
  const color = signalRGB(value);
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-1.5 w-14 rounded-full bg-surface-2">
        <div className="absolute left-1/2 top-0 h-full w-px bg-line/80" />
        <div
          className="absolute top-0 h-full rounded-full"
          style={{ background: `rgb(${color})`, left: pct >= 0 ? "50%" : `${50 + pct}%`, width: `${Math.abs(pct)}%` }}
        />
      </div>
      <span className="tnum w-10 text-right text-xs" style={{ color: `rgb(${color})` }}>
        {fmtSigned(value)}
      </span>
    </div>
  );
}

export function ConfidenceRing({ value, size = 56 }: { value: number; size?: number }) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--surface-2))" strokeWidth={4} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgb(var(--gold))"
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - v)}
        />
      </svg>
      <span className="tnum absolute text-sm font-medium text-text">{(v * 100).toFixed(0)}</span>
    </div>
  );
}
