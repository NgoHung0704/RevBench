import { TriangleAlert } from "lucide-react";

/** Fixed disclaimer — present on every screen (CLAUDE.md hard rule). */
export function Disclaimer() {
  return (
    <footer className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-center gap-2.5 border-t border-line-2 bg-ink/80 px-5 py-2.5 backdrop-blur-md">
      <TriangleAlert size={13} className="shrink-0 text-gold" />
      <p className="text-center text-[0.72rem] text-muted">
        <strong className="font-semibold text-text">Not financial advice</strong> — RevBench is a
        research &amp; education tool. Recommendations are model output, not guidance.
        Batch-computed; no live data.
      </p>
    </footer>
  );
}
