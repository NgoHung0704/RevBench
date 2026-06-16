import { actionBg, cn, type Action } from "@/lib/utils";

export function ActionBadge({ action, className }: { action: Action; className?: string }) {
  const dot = action === "buy" ? "bg-buy" : action === "sell" ? "bg-sell" : "bg-hold";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        actionBg[action],
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      {action}
    </span>
  );
}

export function ConvictionPill({ conviction }: { conviction: string }) {
  return <span className="chip capitalize">{conviction} conviction</span>;
}
