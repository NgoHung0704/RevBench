import type { Recommendation } from "@/lib/types";

function Rule({ color, label }: { color: string; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2.5">
      <span className="h-0.5 w-[18px] rounded" style={{ background: color }} />
      <span
        className="text-[0.62rem] font-semibold uppercase tracking-[0.14em]"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  );
}

export function ThesisCard({ rec }: { rec: Recommendation }) {
  return (
    <div className="rounded-[18px] border border-line bg-surface/60 px-[26px] py-6 shadow-[0_22px_55px_-42px_rgba(0,0,0,0.9)]">
      <Rule color="#d6b27a" label="Strategist thesis" />
      <p className="mb-[22px] text-base leading-[1.66] text-[#dde1ea] [text-wrap:pretty]">
        {rec.thesis || "No strategist narrative was generated for this ticker in the latest run."}
      </p>
      {rec.counterarguments.length > 0 && (
        <>
          <Rule color="#8fa1d8" label="Counterarguments" />
          <div className="flex flex-col gap-3">
            {rec.counterarguments.map((ca, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-info" />
                <p className="text-sm leading-[1.55] text-[#aab2c2] [text-wrap:pretty]">{ca}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
