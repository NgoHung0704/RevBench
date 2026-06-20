"use client";

import { motion, useReducedMotion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";

/** A simple left-origin fill in a rounded track (confidence, cost meter).
 *  `value` in [0,1]. Animates scaleX 0→1 (transform-only, 60fps). */
export function GrowBar({
  value,
  color,
  delay = 0,
  className = "",
  trackClass = "",
}: {
  value: number;
  color: string;
  delay?: number;
  className?: string;
  trackClass?: string;
}) {
  const reduce = useReducedMotion();
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className={`relative overflow-hidden rounded-full ${trackClass}`}>
      <motion.div
        className={`absolute inset-y-0 left-0 rounded-full ${className}`}
        style={{ width: `${v * 100}%`, background: color, transformOrigin: "left" }}
        initial={reduce ? false : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: DUR.draw, ease: EASE, delay }}
      />
    </div>
  );
}

/** A signed bar growing from a centered zero line (component breakdown,
 *  agent strength). `value` is scaled against `max`; ±50% of the track width. */
export function BipolarBar({
  value,
  max = 1,
  posColor,
  negColor,
  delay = 0,
  height = 24,
}: {
  value: number;
  max?: number;
  posColor: string;
  negColor: string;
  delay?: number;
  height?: number;
}) {
  const reduce = useReducedMotion();
  const pos = value >= 0;
  const w = (Math.min(Math.abs(value), max) / max) * 50;
  return (
    <div className="relative w-full" style={{ height }}>
      <div className="absolute left-1/2 top-0 h-full w-px bg-line-2" />
      <motion.div
        className="absolute top-0 bottom-0 rounded-[5px]"
        style={{
          [pos ? "left" : "right"]: "50%",
          width: `${w}%`,
          background: pos ? posColor : negColor,
          transformOrigin: pos ? "left" : "right",
        }}
        initial={reduce ? false : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: DUR.draw, ease: EASE, delay }}
      />
    </div>
  );
}
