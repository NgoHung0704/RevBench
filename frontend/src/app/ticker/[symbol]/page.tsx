import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ShieldAlert } from "lucide-react";
import { TICKERS, UNIVERSE } from "@/lib/mock";
import { fmtCompact, fmtPct, fmtSigned, signalRGB } from "@/lib/utils";
import { ActionBadge, ConvictionPill } from "@/components/Badge";
import { ConfidenceRing, ScoreMeter } from "@/components/Meters";
import { PriceChart } from "@/components/PriceChart";
import { AgentInsight } from "@/components/AgentInsight";

export function generateStaticParams() {
  return UNIVERSE.map((s) => ({ symbol: s.ticker }));
}

export default async function TickerPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const d = TICKERS[symbol?.toUpperCase()];
  if (!d) notFound();
  const { rec } = d;
  const up = d.change1d >= 0;

  return (
    <div className="py-8">
      <Link href="/" className="mb-6 inline-flex items-center gap-2 text-sm text-muted transition hover:text-text">
        <ArrowLeft size={15} /> Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-4xl font-semibold tracking-tight text-text">{d.stock.ticker}</h1>
            <span className="chip">{d.stock.sector}</span>
          </div>
          <p className="mt-1 font-display text-xl text-muted">{d.stock.name}</p>
        </div>
        <div className="text-right">
          <p className="tnum text-3xl text-text">${d.lastClose.toFixed(2)}</p>
          <p className="tnum" style={{ color: up ? "rgb(var(--buy))" : "rgb(var(--sell))" }}>
            {fmtPct(d.change1d)} today
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        {/* Chart */}
        <div className="card p-4">
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="label">Price · 8 months</span>
            <span className="label">candlestick</span>
          </div>
          <PriceChart bars={d.prices} />
        </div>

        {/* Recommendation hero */}
        <div className="card animate-fade-up p-6">
          <div className="flex items-center justify-between">
            <ActionBadge action={rec.action} className="px-3 py-1.5 text-sm" />
            <ConvictionPill conviction={rec.conviction} />
          </div>

          <div className="mt-5 flex items-center gap-5">
            <ConfidenceRing value={rec.confidence} size={64} />
            <div>
              <p className="label">Combined score</p>
              <p className="tnum text-3xl" style={{ color: `rgb(${signalRGB(rec.score)})` }}>
                {fmtSigned(rec.score)}
              </p>
              <p className="label mt-0.5">confidence {(rec.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>

          <div className="mt-4">
            <ScoreMeter value={rec.score} />
          </div>

          <p className="mt-5 text-sm leading-relaxed text-muted">{rec.thesis}</p>

          {rec.counterarguments.length > 0 && (
            <div className="mt-4 rounded-xl border border-line/60 bg-surface-2/40 p-3">
              <p className="label mb-1.5">Counterarguments</p>
              <ul className="space-y-1">
                {rec.counterarguments.map((c, i) => (
                  <li key={i} className="flex gap-2 text-sm text-muted">
                    <span className="text-sell/60">↺</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk row */}
          <div className="mt-5 grid grid-cols-3 gap-3 border-t border-line/50 pt-4">
            <Metric label="Risk" value={rec.riskLevel} />
            <Metric label="Max position" value={`${rec.maxPositionPct}%`} />
            <Metric label="Stop" value={rec.stopLossPct ? `-${rec.stopLossPct}%` : "—"} />
          </div>
          {rec.riskFlags.length > 0 && (
            <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-gold/80">
              <ShieldAlert size={13} /> {rec.riskFlags.join(" · ")}
            </p>
          )}
        </div>
      </div>

      {/* Agent insights */}
      <section className="mt-12">
        <h2 className="border-b border-line/50 pb-2 font-display text-xl tracking-tight">Agent insights</h2>
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {d.signals.map((s) => (
            <AgentInsight key={s.agent} s={s} />
          ))}
        </div>
      </section>

      {/* News + fundamentals */}
      <section className="mt-12 grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="border-b border-line/50 pb-2 font-display text-xl tracking-tight">Scored news</h2>
          <div className="mt-3 space-y-2">
            {d.news.map((n, i) => (
              <div key={i} className="card flex items-start justify-between gap-4 p-4">
                <div>
                  <p className="text-sm text-text">{n.title}</p>
                  <p className="label mt-1">
                    {n.date} · {n.event_type}
                  </p>
                </div>
                <span className="tnum shrink-0 text-sm" style={{ color: `rgb(${signalRGB(n.score)})` }}>
                  {fmtSigned(n.score)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2 className="border-b border-line/50 pb-2 font-display text-xl tracking-tight">
            Fundamentals <span className="label">SEC EDGAR · quarterly</span>
          </h2>
          <div className="card mt-3 overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                {d.fundamentals.map((f, i) => (
                  <tr key={i} className="border-b border-line/30 last:border-0">
                    <td className="px-4 py-2 text-muted">{f.metric}</td>
                    <td className="tnum px-4 py-2 text-faint">{f.period_end}</td>
                    <td className="tnum px-4 py-2 text-right text-text">
                      {f.isEps ? `$${f.value.toFixed(2)}` : fmtCompact(f.value)}
                    </td>
                    <td className="tnum px-4 py-2 text-right">
                      {f.yoy !== null ? (
                        <span style={{ color: `rgb(${signalRGB(f.yoy)})` }}>{fmtPct(f.yoy)}</span>
                      ) : (
                        <span className="text-faint">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="label">{label}</p>
      <p className="mt-0.5 text-sm font-medium capitalize text-text">{value}</p>
    </div>
  );
}
