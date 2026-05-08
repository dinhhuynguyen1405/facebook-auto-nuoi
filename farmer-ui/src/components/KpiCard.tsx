import { cn } from "@/lib/utils";

type Color = "primary" | "emerald" | "amber" | "rose" | "violet" | "orange";

const iconBg: Record<Color, string> = {
  primary: "bg-primary/10 text-primary",
  emerald: "bg-emerald-100 text-emerald-600",
  amber:   "bg-amber-100  text-amber-600",
  rose:    "bg-rose-100   text-rose-600",
  violet:  "bg-violet-100 text-violet-600",
  orange:  "bg-orange-100 text-orange-600",
};
const bar: Record<Color, string> = {
  primary: "bg-primary",
  emerald: "bg-emerald-500",
  amber:   "bg-amber-500",
  rose:    "bg-rose-500",
  violet:  "bg-violet-500",
  orange:  "bg-orange-500",
};

export function KpiCard({
  icon,
  label,
  value,
  sub,
  progress,
  color = "primary",
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  progress?: number;
  color?: Color;
}) {
  return (
    <div className="card p-4 flex flex-col gap-3 hover:shadow-md transition-all">
      <div className="flex items-start justify-between">
        <div className={cn("p-2.5 rounded-xl shrink-0", iconBg[color])}>
          {icon}
        </div>
      </div>
      <div>
        <p className="text-2xl font-black text-slate-900">{value}</p>
        <p className="text-xs font-semibold text-slate-500 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
      {progress !== undefined && (
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", bar[color])}
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}
