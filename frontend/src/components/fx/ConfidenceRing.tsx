"use client";

import { motion, useReducedMotion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";
import { CountUp } from "./CountUp";

/** SVG confidence ring with a stroke-dashoffset draw-in and a count-up center.
 *  `value` in [0,1]. */
export function ConfidenceRing({
  value,
  color,
  size = 118,
  stroke = 9,
}: {
  value: number;
  color: string;
  size?: number;
  stroke?: number;
}) {
  const reduce = useReducedMotion();
  const r = size / 2 - 7;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value));
  const target = c * (1 - v);

  return (
    <div className="relative flex-none" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--line-2))" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={reduce ? false : { strokeDashoffset: c }}
          animate={{ strokeDashoffset: target }}
          transition={{ duration: DUR.draw, ease: EASE, delay: 0.12 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <CountUp
          value={Math.round(v * 100)}
          suffix="%"
          className="font-mono text-2xl font-semibold text-text"
        />
        <span className="mt-0.5 text-[0.6rem] font-semibold uppercase tracking-[0.1em] text-faint">
          confidence
        </span>
      </div>
    </div>
  );
}
