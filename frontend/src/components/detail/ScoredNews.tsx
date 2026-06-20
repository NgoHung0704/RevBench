import type { NewsItem } from "@/lib/types";
import { fmtSignedU, numColor } from "@/lib/colors";

export function ScoredNews({ news }: { news: NewsItem[] }) {
  return (
    <div className="rounded-2xl border border-line bg-surface/60 px-5 py-[18px] shadow-[0_22px_50px_-42px_rgba(0,0,0,0.85)]">
      <h2 className="mb-3.5 text-[0.94rem] font-bold">Scored news</h2>
      {news.length > 0 ? (
        <div className="flex flex-col">
          {news.map((n, i) => (
            <div key={i} className="flex gap-3.5 border-t border-line-2 py-3 first:border-t-0">
              <div className="w-11 flex-none text-center">
                <div className="font-mono text-[0.82rem] font-semibold" style={{ color: numColor(n.score) }}>
                  {fmtSignedU(n.score, 2)}
                </div>
                <div className="mt-0.5 text-[0.6rem] text-faint-2">{Math.round(n.confidence * 100)}%</div>
              </div>
              <div className="min-w-0">
                <p className="mb-1 text-[0.84rem] leading-[1.45] text-[#dde1ea] [text-wrap:pretty]">{n.title}</p>
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-[0.7rem] text-faint">{n.date}</span>
                  <span className="rounded-[5px] border border-line-2 bg-ink/50 px-1.5 py-px text-[0.62rem] font-semibold uppercase tracking-wide text-[#8a93a3]">
                    {n.event_type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-line-2 px-4 py-6 text-center">
          <div className="mb-1.5 font-mono text-sm text-muted">n = 0</div>
          <p className="text-[0.78rem] leading-[1.5] text-faint">
            No headlines cleared the scoring threshold in the current window. We show the gap
            honestly rather than fill it.
          </p>
        </div>
      )}
    </div>
  );
}
