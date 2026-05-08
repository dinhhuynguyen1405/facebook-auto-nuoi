import { useCallback, useState } from "react";
import {
  Users, CheckCircle2, AlertTriangle, Activity,
  Zap, Play, StopCircle, RefreshCw, Clock, CalendarDays,
} from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { cn, formatDate } from "@/lib/utils";
import { KpiCard } from "@/components/KpiCard";
import { StatusBadge } from "@/components/StatusBadge";
import { TopBar } from "@/components/TopBar";
import { PageLoader } from "@/components/Spinner";

export function DashboardPage() {
  const { data: stats, loading: statsLoading, refetch: refetchStats } = useApi(api.getStats);
  const { data: accounts, loading: accLoading, refetch: refetchAccs } = useApi(api.getAccounts);
  const { data: scheduler, refetch: refetchSched } = useApi(api.getSchedulerStatus);
  const { data: logs } = useApi(api.getLogs);

  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [acting, setActing] = useState(false);

  const loading = statsLoading || accLoading;

  const refetchAll = useCallback(() => {
    refetchStats(); refetchAccs(); refetchSched();
  }, [refetchStats, refetchAccs, refetchSched]);

  const doAction = async (fn: () => Promise<{ success: boolean; message: string }>) => {
    setActing(true); setActionMsg(null);
    try {
      const r = await fn();
      setActionMsg(r.message);
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Lỗi");
    } finally {
      setActing(false);
      setTimeout(() => { refetchAll(); setActionMsg(null); }, 1500);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Dashboard"
        subtitle="Tổng quan hệ thống nuôi nick"
        onRefresh={refetchAll}
        refreshing={loading}
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? <PageLoader /> : (
          <>
            {/* KPI row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <KpiCard icon={<Users className="w-5 h-5" />}     label="Tổng nick"        value={stats?.total_accounts ?? 0}   color="primary" />
              <KpiCard icon={<CheckCircle2 className="w-5 h-5" />} label="Đang hoạt động" value={stats?.active_accounts ?? 0}  color="emerald" />
              <KpiCard icon={<AlertTriangle className="w-5 h-5" />} label="Checkpoint"    value={stats?.checkpoint_accounts ?? 0} color="orange" />
              <KpiCard
                icon={<Activity className="w-5 h-5" />}
                label="Seeding bật"
                value={stats?.seeding_enabled ?? 0}
                sub={`Avg ngày nuôi: ${stats?.avg_day?.toFixed(1) ?? 0}`}
                color="violet"
                progress={stats ? (stats.seeding_enabled / Math.max(stats.total_accounts, 1)) * 100 : 0}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Scheduler panel */}
              <div className="card p-5 flex flex-col gap-4">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-primary/10"><Zap className="w-4 h-4 text-primary" /></div>
                  <div>
                    <p className="text-sm font-bold text-slate-800">Scheduler</p>
                    <p className="text-xs text-slate-400">APScheduler daemon</p>
                  </div>
                  <span className={cn(
                    "badge ml-auto",
                    scheduler?.running ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                  )}>
                    {scheduler?.running ? "● Đang chạy" : "○ Dừng"}
                  </span>
                </div>

                {scheduler?.next_run && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2">
                    <Clock className="w-3.5 h-3.5 shrink-0" />
                    <span>Lần chạy tiếp: <strong className="text-slate-700">{formatDate(scheduler.next_run)}</strong></span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2">
                  <CalendarDays className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    Hàng ngày lúc{" "}
                    <strong className="text-slate-700">
                      {String(scheduler?.hour ?? 9).padStart(2,"0")}:{String(scheduler?.minute ?? 30).padStart(2,"0")}
                    </strong>
                    {" "}({scheduler?.timezone ?? "Asia/Ho_Chi_Minh"})
                  </span>
                </div>

                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => doAction(scheduler?.running ? api.stopScheduler : api.startScheduler)}
                    disabled={acting}
                    className={cn(
                      "btn flex-1 justify-center",
                      scheduler?.running
                        ? "bg-red-50 text-red-600 hover:bg-red-100"
                        : "btn-primary"
                    )}
                  >
                    {scheduler?.running
                      ? <><StopCircle className="w-4 h-4" /> Dừng</>
                      : <><Play className="w-4 h-4" /> Khởi động</>}
                  </button>
                  <button
                    onClick={() => doAction(api.triggerNow)}
                    disabled={acting}
                    className="btn bg-amber-50 text-amber-700 hover:bg-amber-100"
                    title="Trigger ngay 1 lần"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Run Now
                  </button>
                </div>

                {actionMsg && (
                  <p className="text-xs text-center text-emerald-600 font-semibold bg-emerald-50 rounded-xl py-1.5">
                    {actionMsg}
                  </p>
                )}
              </div>

              {/* Recent accounts */}
              <div className="card p-5 lg:col-span-2 flex flex-col gap-3">
                <p className="text-sm font-bold text-slate-800">Nick gần đây</p>
                <div className="space-y-2">
                  {(accounts ?? []).slice(0, 5).map(acc => (
                    <div key={acc.user_id} className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
                      <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                        <span className="text-xs font-bold text-primary">{acc.name.charAt(0).toUpperCase()}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-slate-800 truncate">{acc.name}</p>
                        <p className="text-xs text-slate-400 truncate">{acc.plan_notes}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <StatusBadge status={acc.status} />
                        <p className="text-xs text-slate-400 mt-0.5">Ngày {acc.day_number}</p>
                      </div>
                    </div>
                  ))}
                  {(!accounts || accounts.length === 0) && (
                    <p className="text-sm text-slate-400 text-center py-4">Chưa có account nào</p>
                  )}
                </div>
              </div>
            </div>

            {/* Recent logs */}
            <div className="card p-5">
              <p className="text-sm font-bold text-slate-800 mb-3">Logs gần nhất</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-100">
                      <th className="pb-2 font-semibold">Account</th>
                      <th className="pb-2 font-semibold">Action</th>
                      <th className="pb-2 font-semibold">Kết quả</th>
                      <th className="pb-2 font-semibold">Ngày</th>
                      <th className="pb-2 font-semibold">Thời gian</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(logs ?? []).slice(0, 8).map(log => (
                      <tr key={log.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                        <td className="py-2 font-semibold text-slate-700">{log.account_id}</td>
                        <td className="py-2 text-slate-500">{log.action}</td>
                        <td className="py-2">
                          <span className={cn(
                            "badge text-[11px]",
                            log.result === "ok"         ? "bg-emerald-100 text-emerald-700" :
                            log.result === "checkpoint" ? "bg-orange-100 text-orange-700"  :
                                                          "bg-red-100 text-red-700"
                          )}>{log.result}</span>
                        </td>
                        <td className="py-2 text-slate-500">{log.day_number}</td>
                        <td className="py-2 text-slate-400">{formatDate(log.created_at)}</td>
                      </tr>
                    ))}
                    {(!logs || logs.length === 0) && (
                      <tr><td colSpan={5} className="py-6 text-center text-slate-400">Chưa có log</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
