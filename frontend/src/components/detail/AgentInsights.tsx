"use client";

import { motion, useReducedMotion } from "framer-motion";
import { DUR, EASE } from "@/lib/motion";
import type { AgentName, AgentSignal } from "@/lib/types";

const ORDER: AgentName[] = ["news", "technical", "fundamentals"];

function sigMeta(signal: number) {
  const color = signal > 0 ? "#38c98a" : signal < 0 ? "#f4646e" : "#818c9f";
  const label = signal > 0.15 ? "Bullish" : signal < -0.15 ? "Bearish" : "Neutral";
  const bg =
    signal > 0 ? "rgba(56,201,138,0.12)" : signal < 0 ? "rgba(244,100,110,0.12)" : "rgba(129,140,159,0.12)";
  return { color, label, bg };
}

function StrengthBar({ signal, color, delay }: { signal: number; color: string; delay: number }) {
  const reduce = useReducedMotion();
  const pos = signal >= 0;
  const w = Math.min(Math.abs(signal), 1) * 50;
  return (
    <div className="relative h-[5px] flex-1 rounded-full bg-line-2">
      <div className="absolute left-1/2 top-0 h-full w-px bg-line-2" />
      <motion.div
        className="absolute top-0 bottom-0 rounded-full"
        style={{ [pos ? "left" : "right"]: "50%", width: `${w}%`, background: color, transformOrigin: pos ? "left" : "right" }}
        initial={reduce ? false : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: DUR.draw, ease: EASE, delay }}
      />
    </div>
  );
}

function Card({ name, signal, index }: { name: AgentName; signal?: AgentSignal; index: number }) {
  const empty = !signal;
  const sig = signal?.signal ?? 0;
  const meta = sigMeta(sig);
  const chips: { k: string; v: string }[] = [];
  if (signal?.regime) chips.push({ k: "Regime", v: signal.regime });
  if (signal?.valuation_view) chips.push({ k: "Valuation", v: signal.valuation_view });
  if (signal?.growth_view) chips.push({ k: "Growth", v: signal.growth_view });

  return (
    <div className="rounded-[14px] border border-line bg-surface/55 p-4 shadow-[0_18px_40px_-40px_rgba(0,0,0,0.85)]">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[0.7rem] font-bold uppercase tracking-[0.1em] text-[#cdd3df]">{name}</span>
        <span
          className="inline-flex items-center gap-1.5 rounded-[7px] px-2 py-0.5 text-[0.7rem] font-semibold"
          style={{ background: meta.bg, color: meta.color }}
        >
          {meta.label}
        </span>
      </div>
      {empty ? (
        <div className="rounded-[10px] border border-dashed border-line-2 px-3 py-3.5 text-center">
          <div className="mb-1 font-mono text-[0.82rem] text-muted">n = 0</div>
          <p className="text-xs leading-[1.5] text-faint">
            No scored signals in the current window. The agent abstains rather than guess.
          </p>
        </div>
      ) : (
        <>
          <div className="mb-3 flex items-center gap-2.5">
            <StrengthBar signal={sig} color={meta.color} delay={0.26 + index * 0.05} />
            <span className="whitespace-nowrap text-[0.66rem] text-faint">
              conf {Math.round(signal.confidence * 100)}%
            </span>
          </div>
          <p className="mb-3 text-[0.81rem] leading-[1.55] text-[#aab2c2] [text-wrap:pretty]">
            {signal.rationale ?? signal.summary ?? "—"}
          </p>
          {chips.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {chips.map((c) => (
                <span
                  key={c.k}
                  className="rounded-md border border-line-2 bg-ink/50 px-2 py-1 text-[0.66rem] font-medium capitalize text-[#8a93a3]"
                >
                  {c.k} <span className="text-[#cdd3df]">{c.v}</span>
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function AgentInsights({ signals }: { signals: AgentSignal[] }) {
  const byName = new Map(signals.map((s) => [s.agent, s]));
  return (
    <div>
      <h2 className="mb-3.5 text-[0.94rem] font-bold">Agent insights</h2>
      <div className="grid gap-3.5 md:grid-cols-3">
        {ORDER.map((name, i) => (
          <Card key={name} name={name} signal={byName.get(name)} index={i} />
        ))}
      </div>
    </div>
  );
}
