"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "framer-motion";

const MINUS = "−"; // unicode minus, matches the prototype's number formatting

function format(
  v: number,
  decimals: number,
  prefix: string,
  suffix: string,
  signed: boolean,
): string {
  const body = Math.abs(v).toFixed(decimals);
  let pre = prefix;
  if (signed) pre = (v >= 0 ? "+" : MINUS) + prefix;
  else if (v < 0) pre = MINUS + prefix;
  return pre + body + suffix;
}

/** Animated count-up. The final value is rendered in the DOM from the first
 *  paint (SSR / no-JS / screen-reader / reduced-motion all read the real
 *  number); the animation only runs on top after mount. */
export function CountUp({
  value,
  decimals = 0,
  prefix = "",
  suffix = "",
  signed = false,
  durationMs = 650,
  className,
}: {
  value: number | null | undefined;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  signed?: boolean;
  durationMs?: number;
  className?: string;
}) {
  const fmt = (v: number) => format(v, decimals, prefix, suffix, signed);
  // Missing values render an honest em-dash rather than a fabricated 0.
  const safe = value ?? null;
  const [display, setDisplay] = useState(() => (safe == null ? "—" : fmt(safe)));
  const reduce = useReducedMotion();

  useEffect(() => {
    if (safe == null) {
      setDisplay("—");
      return;
    }
    if (reduce) {
      setDisplay(fmt(safe));
      return;
    }
    let raf = 0;
    let t0: number | null = null;
    const step = (now: number) => {
      if (t0 === null) t0 = now;
      let p = Math.min((now - t0) / durationMs, 1);
      p = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setDisplay(fmt(safe * p));
      if (p < 1) raf = requestAnimationFrame(step);
      else setDisplay(fmt(safe));
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [safe, reduce, durationMs, decimals, prefix, suffix, signed]);

  return <span className={className}>{display}</span>;
}
