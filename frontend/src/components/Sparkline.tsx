"use client";

import { motion, useReducedMotion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";
import type { Bar } from "@/lib/types";

/** Last-N closes as a stroke that draws itself in once on mount. */
export function Sparkline({
  bars,
  color,
  delay = 0,
  count = 32,
  height = 42,
}: {
  bars: Bar[];
  color: string;
  delay?: number;
  count?: number;
  height?: number;
}) {
  const reduce = useReducedMotion();
  const closes = bars.slice(-count).map((b) => b.close);
  if (closes.length < 2) return <div style={{ height }} />;

  const W = 250;
  const pad = 4;
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const pts = closes
    .map((c, i) => {
      const x = (i / (closes.length - 1)) * W;
      const y = pad + (1 - (c - min) / span) * (height - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" width="100%" height={height} aria-hidden>
      <motion.polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={reduce ? false : { pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: DUR.draw + 0.15, ease: EASE, delay }}
      />
    </svg>
  );
}
