import { useState } from "react";
import { CheckCircle2, XCircle, Clock, Layers } from "lucide-react";
import { api, type DayPlan } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { cn } from "@/lib/utils";
import { TopBar } from "@/components/TopBar";
import { PageLoader } from "@/components/Spinner";

const WEEK_COLOR: Record<number, { bar: string; label: string; bg: string; dot: string }> = {
  1: { bar: "bg-blue-500",   label: "Tuần 1 — Người mới",   bg: "bg-blue-50",   dot: "bg-blue-500"   },
  2: { bar: "bg-violet-500", label: "Tuần 2 — Làm quen",    bg: "bg-violet-50", dot: "bg-violet-500" },
  3: { bar: "bg-amber-500",  label: "Tuần 3 — Hoà nhập",    bg: "bg-amber-50",  dot: "bg-amber-500"  },
  4: { bar: "bg-emerald-500",label: "Tuần 4+ — Người thật", bg: "bg-emerald-50",dot: "bg-emerald-500"},
};
const weekOf = (day: number) => day <= 7 ? 1 : day <= 14 ? 2 : day <= 21 ? 3 : 4;

function PlanCard({ plan, selected, onClick }: { plan: DayPlan; selected: boolean; onClick: () => void }) {
  const wk = WEEK_COLOR[weekOf(plan.day)];
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left card p-3 flex flex-col gap-2 transition-all duration-150 cursor-pointer",
        selected ? "border-primary shadow-md shadow-primary/10" : "hover:border-slate-300 hover:shadow"
      )}
    >
      <div className="flex items-center justify-between">
        <span className={cn("text-lg font-black", selected ? "text-primary" : "text-slate-700")}>
          Ngày {plan.day}
        </span>
        <div className="flex items-center gap-1.5">
          <span className={cn("badge text-[10px]", plan.allow_seeding ? "bg-primary/10 text-primary" : "bg-slate-100 text-slate-400")}>
            {plan.allow_seeding ? "Seeding ✅" : "🚫"}
          </span>
        </div>
      </div>
      <div className={cn("w-full h-1 rounded-full", wk.bar)} />
      <div className="flex items-center gap-3 text-[11px] text-slate-500">
        <span className="flex items-center gap-1"><Layers className="w-3 h-3" />{plan.sessions} phiên</span>
        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{plan.window}</span>
      </div>
      <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{plan.notes}</p>
    </button>
  );
}

function PlanDetail({ plan }: { plan: DayPlan }) {
  const wk = WEEK_COLOR[weekOf(plan.day)];
  const totalWeight = plan.actions.reduce((s, [, w]) => s + w, 0);

  return (
    <div className="card p-5 flex flex-col gap-4 sticky top-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={cn("p-3 rounded-2xl", wk.bg)}>
          <span className="text-2xl font-black text-slate-800">{plan.day}</span>
        </div>
        <div className="flex-1">
          <p className="text-base font-bold text-slate-900">Ngày {plan.day}</p>
          <p className={cn("badge mt-1", wk.bg, "text-slate-700")}>{wk.label}</p>
        </div>
      </div>

      {/* Meta */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Phiên/ngày",  value: plan.sessions,                 icon: <Layers className="w-4 h-4" /> },
          { label: "Khung giờ",   value: plan.window,                   icon: <Clock className="w-4 h-4" />  },
          { label: "Seeding",     value: plan.allow_seeding ? "Có" : "Không",
            icon: plan.allow_seeding ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" /> },
        ].map(({ label, value, icon }) => (
          <div key={label} className="bg-slate-50 rounded-xl p-2.5 text-center">
            <div className="flex justify-center text-slate-500 mb-1">{icon}</div>
            <p className="text-sm font-bold text-slate-800">{value}</p>
            <p className="text-[10px] text-slate-400">{label}</p>
          </div>
        ))}
      </div>

      {/* Notes */}
      <p className="text-xs text-slate-600 bg-slate-50 rounded-xl px-3 py-2.5 leading-relaxed">{plan.notes}</p>

      {/* Action breakdown */}
      <div>
        <p className="text-xs font-bold text-slate-700 mb-2.5">Action pool ({plan.actions.length} loại)</p>
        <div className="space-y-2">
          {plan.actions.sort((a, b) => b[1] - a[1]).map(([name, weight]) => {
            const pct = Math.round((weight / totalWeight) * 100);
            return (
              <div key={name}>
                <div className="flex justify-between text-[11px] mb-0.5">
                  <span className="text-slate-600 font-mono truncate max-w-[70%]">{name}</span>
                  <span className="font-bold text-slate-700">{pct}%</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={cn("h-full rounded-full", wk.bar)}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function SchedulePage() {
  const { data: plans, loading, refetch } = useApi(api.getSchedule);
  const [selected, setSelected] = useState<number>(1);

  const selectedPlan = (plans ?? []).find(p => p.day === selected);
  const weeks = [1, 2, 3, 4].map(w => ({
    w,
    plans: (plans ?? []).filter(p => weekOf(p.day) === w),
    ...WEEK_COLOR[w],
  }));

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Lịch 30 ngày"
        subtitle="Kế hoạch hành động chi tiết từng ngày nuôi nick"
        onRefresh={refetch}
        refreshing={loading}
      />

      <div className="flex-1 overflow-y-auto p-6">
        {loading ? <PageLoader /> : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Plan list by week */}
            <div className="lg:col-span-2 space-y-6">
              {weeks.map(({ w, label, plans: wPlans, dot }) => (
                <div key={w}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className={cn("w-2.5 h-2.5 rounded-full", dot)} />
                    <p className="text-sm font-bold text-slate-700">{label}</p>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {wPlans.map(p => (
                      <PlanCard
                        key={p.day}
                        plan={p}
                        selected={selected === p.day}
                        onClick={() => setSelected(p.day)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Right: Detail */}
            <div>
              {selectedPlan
                ? <PlanDetail plan={selectedPlan} />
                : <div className="card p-8 text-center text-slate-400"><p>Chọn 1 ngày để xem chi tiết</p></div>
              }
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
