"use client";

import { MotionConfig } from "framer-motion";

/** App-wide motion config: framer honors `prefers-reduced-motion` automatically
 *  (transform/layout animations drop to instant; opacity is kept). */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
