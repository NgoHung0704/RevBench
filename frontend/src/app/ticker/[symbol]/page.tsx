import { getTicker } from "@/lib/api";
import { fmtMoney, fmtPctU, numColor } from "@/lib/colors";
import { Reveal } from "@/components/fx/Reveal";
import { RecHero } from "@/components/detail/RecHero";
import { ThesisCard } from "@/components/detail/ThesisCard";
import { PriceSection } from "@/components/detail/PriceSection";
import { Breakdown } from "@/components/detail/Breakdown";
import { AgentInsights } from "@/components/detail/AgentInsights";
import { ScoredNews } from "@/components/detail/ScoredNews";
import { Fundamentals } from "@/components/detail/Fundamentals";
import { ApiDown } from "@/components/ApiDown";

export const dynamic = "force-dynamic";

export default async function TickerPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const d = await getTicker(symbol);
  if (!d) return <ApiDown />;
  const { rec } = d;

  return (
    <div className="mx-auto max-w-detail px-5 pb-10 pt-[26px] sm:px-7">
      {/* symbol head */}
      <Reveal className="mb-5 flex flex-wrap items-end justify-between gap-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-[1.85rem] font-semibold tracking-[0.01em]">{d.stock.ticker}</h1>
            <span className="rounded-md border border-line px-2 py-0.5 text-[0.7rem] font-semibold tracking-wide text-muted">
              {d.stock.sector}
            </span>
          </div>
          <div className="mt-1.5 text-[0.94rem] text-muted">{d.stock.name}</div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[1.6rem] font-semibold">{fmtMoney(d.lastClose)}</div>
          <div className="mt-0.5 font-mono text-[0.8rem] font-medium" style={{ color: numColor(d.change1d) }}>
            {fmtPctU(d.change1d)} today
          </div>
        </div>
      </Reveal>

      {/* hero: recommendation + thesis */}
      <Reveal delay={0.06} className="mb-4 grid items-stretch gap-4 lg:grid-cols-[minmax(320px,0.9fr)_1.3fr]">
        <RecHero rec={rec} />
        <ThesisCard rec={rec} />
      </Reveal>

      <Reveal delay={0.15} className="mb-4">
        <PriceSection bars={d.prices} ticker={d.stock.ticker} lastClose={d.lastClose} />
      </Reveal>

      <Reveal delay={0.19} className="mb-4">
        <Breakdown components={rec.components} />
      </Reveal>

      <Reveal delay={0.23} className="mb-4">
        <AgentInsights signals={d.signals} />
      </Reveal>

      <Reveal delay={0.27} className="grid gap-4 lg:grid-cols-[1.05fr_1fr]">
        <ScoredNews news={d.news} />
        <Fundamentals rows={d.fundamentals} />
      </Reveal>
    </div>
  );
}
