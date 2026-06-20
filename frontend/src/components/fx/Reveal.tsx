"use client";

import { motion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";

/** Fade-up entrance for a section/card. Under reduced-motion (MotionConfig)
 *  the translate is dropped and only opacity animates. */
export function Reveal({
  children,
  delay = 0,
  y = 12,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  y?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: DUR.enter, ease: EASE, delay }}
    >
      {children}
    </motion.div>
  );
}
