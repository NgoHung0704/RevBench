import Link from "next/link";
import { ALL, COST } from "@/lib/mock";
import { fmtSigned, signalRGB } from "@/lib/utils";
import { TickerCard } from "@/components/TickerCard";
import { SignalBar } from "@/components/Meters";

export default function Dashboard() {
  const ranked = [...ALL].sort((a, b) => b.rec.score - a.rec.score);
  const buys = ALL.filter((d) => d.rec.action === "buy").length;
  const sells = ALL.filter((d) => d.rec.action === "sell").length;
  const holds = ALL.length - buys - sells;
  const top = ranked[0];

  return (
    <div className="py-8">
      {/* Hero */}
      <section className="animate-fade-up">
        <p className="label text-gold/70">Daily recommendations · as of 2026-06-11</p>
        <h1 className="mt-3 max-w-2xl font-display text-4xl leading-[1.1] tracking-tight text-text sm:text-5xl">
          Where the <span className="italic text-gold">agents</span> and the model agree.
        </h1>
        <p className="mt-4 max-w-xl text-muted">
          Seven LLM agents and a LightGBM model, fused into one explainable Buy / Hold / Sell per
          blue-chip — with the full reasoning trail. Decision support, not advice.
        </p>
      </section>

      {/* Pulse strip */}
      <section className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Buy" value={buys} accent="buy" />
        <Stat label="Hold" value={holds} accent="hold" />
        <Stat label="Sell" value={sells} accent="sell" />
        <div className="card flex flex-col justify-center p-4">
          <p className="label">Top conviction</p>
          <Link href={`/ticker/${top.stock.ticker}`} className="mt-1 flex items-baseline gap-2 hover:text-gold">
            <span className="font-mono text-lg font-semibold">{top.stock.ticker}</span>
            <span className="tnum text-sm text-buy">{fmtSigned(top.rec.score)}</span>
          </Link>
        </div>
      </section>

      {/* Recommendation grid */}
      <section className="mt-10">
        <SectionTitle title="Conviction board" hint="ranked by combined signal" />
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {ranked.map((d) => (
            <TickerCard key={d.stock.ticker} d={d} />
          ))}
        </div>
      </section>

      {/* Agent heatmap */}
      <section className="mt-12">
        <SectionTitle title="Agent signal matrix" hint="per-agent view across the universe" />
        <div className="card mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-line/60 text-left">
                {["Ticker", "News", "Technical", "Fundamentals", "Combined"].map((h) => (
                  <th key={h} className="label px-4 py-3 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranked.map((d) => (
                <tr key={d.stock.ticker} className="border-b border-line/30 transition hover:bg-surface-2/40">
                  <td className="px-4 py-2.5">
                    <Link href={`/ticker/${d.stock.ticker}`} className="font-mono font-medium hover:text-gold">
                      {d.stock.ticker}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5">
                    <SignalBar value={d.rec.components.news} />
                  </td>
                  <td className="px-4 py-2.5">
                    <SignalBar value={d.rec.components.technical} />
                  </td>
                  <td className="px-4 py-2.5">
                    <SignalBar value={d.rec.components.fundamentals} />
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="tnum font-medium" style={{ color: `rgb(${signalRGB(d.rec.score)})` }}>
                      {fmtSigned(d.rec.score)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-faint">
          LLM spend today ${COST.today.toFixed(4)} · {COST.calls} calls · batch-run off-peak. The
          agent-alpha question is still data-gated — see the project notes.
        </p>
      </section>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: number; accent: "buy" | "hold" | "sell" }) {
  const color = accent === "buy" ? "text-buy" : accent === "sell" ? "text-sell" : "text-hold";
  return (
    <div className="card p-4">
      <p className="label">{label}</p>
      <p className={`tnum mt-1 text-3xl ${color}`}>{value}</p>
    </div>
  );
}

function SectionTitle({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="flex items-baseline justify-between border-b border-line/50 pb-2">
      <h2 className="font-display text-xl tracking-tight text-text">{title}</h2>
      <span className="label">{hint}</span>
    </div>
  );
}
