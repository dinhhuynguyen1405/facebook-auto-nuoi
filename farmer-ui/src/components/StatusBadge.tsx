import { cn, STATUS_COLOR, STATUS_LABEL } from "@/lib/utils";

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("badge", STATUS_COLOR[status] ?? "bg-slate-100 text-slate-600")}>
      {status === "active" && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 pulse-green" />
      )}
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}
