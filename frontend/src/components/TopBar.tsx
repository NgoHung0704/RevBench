"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import type { CostSummary } from "@/lib/types";
import { GrowBar } from "@/components/fx/Bars";
import { CountUp } from "@/components/fx/CountUp";

const CEILING = 1.0; // hard daily LLM budget ($/day)

export function TopBar({ cost, asOf }: { cost: CostSummary | null; asOf: string | null }) {
  const pathname = usePathname();
  const onDetail = pathname?.startsWith("/ticker/");
  const symbol = onDetail ? decodeURIComponent(pathname.split("/")[2] ?? "") : "";

  return (
    <header className="sticky top-0 z-40 flex items-center gap-4 border-b border-line-2 bg-ink/70 px-5 py-3.5 backdrop-blur-xl sm:px-7">
      <Link href="/" className="flex items-center gap-3">
        <span
          className="grid h-[26px] w-[26px] place-items-center rounded-[7px] font-mono text-sm font-semibold text-[#1a1206]"
          style={{
            background: "linear-gradient(150deg,#d6b27a,#b8915a)",
            boxShadow: "0 0 0 1px rgba(214,178,122,0.35), 0 6px 18px -8px rgba(214,178,122,0.6)",
          }}
        >
          R
        </span>
        <span className="text-base font-bold tracking-tight text-text">RevBench</span>
        <span className="hidden rounded-[5px] border border-line px-1.5 py-0.5 text-[0.62rem] font-semibold uppercase tracking-[0.16em] text-faint sm:inline">
          Research
        </span>
      </Link>

      {onDetail && (
        <div className="flex items-center gap-2.5">
          <span className="text-line">/</span>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-[0.8rem] font-semibold text-muted transition hover:text-text"
          >
            <ArrowLeft size={14} /> Board
          </Link>
          <span className="text-line">/</span>
          <span className="font-mono text-[0.83rem] font-semibold text-gold">{symbol}</span>
        </div>
      )}

      <div className="ml-auto flex items-center gap-4 sm:gap-5">
        {asOf && (
          <div className="hidden items-center gap-2 sm:flex">
            <span className="text-[0.62rem] font-semibold uppercase tracking-[0.13em] text-faint">
              As of
            </span>
            <span className="font-mono text-[0.78rem] text-muted">{asOf}</span>
          </div>
        )}
        {cost && (
          <div className="flex items-center gap-2.5 rounded-[9px] border border-line bg-surface-2/55 py-1.5 pl-3 pr-2.5">
            <span className="text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-faint">
              Today
            </span>
            <GrowBar
              value={Math.min(cost.today / CEILING, 1)}
              color="linear-gradient(90deg,#d6b27a,#e0c089)"
              delay={0.12}
              trackClass="h-1.5 w-[74px] bg-line-2"
            />
            <CountUp
              value={cost.today}
              decimals={2}
              prefix="$"
              durationMs={900}
              className="font-mono text-[0.78rem] text-text"
            />
            <span className="font-mono text-[0.7rem] text-faint">/ $1.00</span>
          </div>
        )}
      </div>
    </header>
  );
}
