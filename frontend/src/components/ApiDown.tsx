import { PlugZap } from "lucide-react";
import { API_BASE } from "@/lib/api";

export function ApiDown() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-content items-center justify-center px-5 py-16">
      <div className="card max-w-md p-8 text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl border border-gold/30 bg-gold/10 text-gold">
          <PlugZap size={22} />
        </span>
        <h2 className="mt-4 text-xl font-bold text-text">Backend not reachable</h2>
        <p className="mt-2 text-sm text-muted">
          The dashboard reads precomputed data from the RevBench API at{" "}
          <span className="font-mono text-faint">{API_BASE}</span>. Start it:
        </p>
        <pre className="mt-4 overflow-x-auto rounded-lg border border-line bg-ink/60 p-3 text-left text-xs text-muted">
          uvicorn backend.app.main:app --port 8000
        </pre>
      </div>
    </div>
  );
}
