import type { Bar } from "@/lib/types";

export function Sparkline({ bars, up, width = 120, height = 36 }: { bars: Bar[]; up: boolean; width?: number; height?: number }) {
  const closes = bars.slice(-40).map((b) => b.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const stepX = width / (closes.length - 1);
  const pts = closes.map((c, i) => `${i * stepX},${height - ((c - min) / span) * (height - 4) - 2}`);
  const color = up ? "rgb(var(--buy))" : "rgb(var(--sell))";
  const id = `spark-${up ? "u" : "d"}-${Math.round(min)}`;
  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline points={`0,${height} ${pts.join(" ")} ${width},${height}`} fill={`url(#${id})`} stroke="none" />
      <polyline points={pts.join(" ")} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
