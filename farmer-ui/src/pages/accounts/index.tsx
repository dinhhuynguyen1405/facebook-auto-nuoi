import { useState } from "react";
import {
  Play, RotateCcw, PowerOff, CheckCircle, AlertTriangle,
  ChevronDown, ChevronUp, Info,
} from "lucide-react";
import { api, type Account } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { cn, formatDate, dayPhase } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";
import { TopBar } from "@/components/TopBar";
import { PageLoader } from "@/components/Spinner";

function AccountCard({ acc, onAction }: { acc: Account; onAction: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const phase = dayPhase(acc.day_number);

  const act = async (fn: () => Promise<{ success: boolean; message: string }>) => {
    setLoading(true); setMsg(null);
    try {
      const r = await fn();
      setMsg(r.message);
      setTimeout(() => { onAction(); setMsg(null); }, 1500);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Lỗi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn(
      "card overflow-hidden transition-all duration-200",
      acc.status === "checkpoint" && "border-orange-200",
      acc.status === "banned" && "border-red-200 opacity-70",
    )}>
      {/* Header row */}
      <div className="p-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0 font-black text-primary text-base">
          {acc.name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-bold text-slate-900 truncate">{acc.name}</p>
            <StatusBadge status={acc.status} />
            {acc.allow_seeding && (
              <span className="badge bg-primary/10 text-primary text-[11px]">Seeding ✅</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">ID: {acc.user_id}</p>
        </div>

        {/* Day badge */}
        <div className="text-center shrink-0">
          <div className="text-2xl font-black text-slate-800">{acc.day_number}</div>
          <div className="text-[10px] text-slate-400 font-semibold">ngày</div>
        </div>

        <button onClick={() => setExpanded(e => !e)} className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-slate-100 text-slate-400 ml-1">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Progress bar (day 1-30) */}
      <div className="px-4 pb-2">
        <div className="flex items-center justify-between mb-1">
          <span className={cn("badge text-[11px]", phase.color)}>{phase.label}</span>
          <span className="text-[11px] text-slate-400">{Math.min(acc.day_number, 30)}/30 ngày</span>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-500"
            style={{ width: `${Math.min((acc.day_number / 30) * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Plan note */}
      <div className="px-4 pb-3 flex items-start gap-1.5">
        <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
        <p className="text-xs text-slate-500 leading-relaxed">{acc.plan_notes}</p>
      </div>

      {/* Actions */}
      <div className="px-4 pb-4 flex gap-2 flex-wrap">
        <button
          onClick={() => act(() => api.runAccount(acc.user_id))}
          disabled={loading || acc.status === "banned"}
          className="btn-primary text-xs py-1.5 px-3"
        >
          <Play className="w-3.5 h-3.5" /> Chạy ngay
        </button>
        <button
          onClick={() => act(() => api.setStatus(acc.user_id, acc.status === "active" ? "inactive" : "active"))}
          disabled={loading}
          className="btn bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs py-1.5 px-3"
        >
          <PowerOff className="w-3.5 h-3.5" />
          {acc.status === "active" ? "Tạm dừng" : "Kích hoạt"}
        </button>
        {acc.status === "checkpoint" && (
          <button
            onClick={() => act(() => api.setStatus(acc.user_id, "active"))}
            disabled={loading}
            className="btn bg-orange-50 text-orange-700 hover:bg-orange-100 text-xs py-1.5 px-3"
          >
            <CheckCircle className="w-3.5 h-3.5" /> Xóa checkpoint
          </button>
        )}
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-white rounded-xl p-3 border border-slate-100">
              <p className="text-slate-400 mb-0.5">Chạy lần cuối</p>
              <p className="font-semibold text-slate-700">{formatDate(acc.last_run)}</p>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-100">
              <p className="text-slate-400 mb-0.5">Checkpoint count</p>
              <p className={cn("font-semibold", acc.checkpoint_count > 0 ? "text-orange-600" : "text-emerald-600")}>
                {acc.checkpoint_count} lần
              </p>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-100">
              <p className="text-slate-400 mb-0.5">Phiên / ngày</p>
              <p className="font-semibold text-slate-700">{acc.sessions_today} phiên</p>
            </div>
            <div className="bg-white rounded-xl p-3 border border-slate-100">
              <p className="text-slate-400 mb-0.5">Seeding link</p>
              <p className={cn("font-semibold", acc.allow_seeding ? "text-primary" : "text-slate-400")}>
                {acc.allow_seeding ? "Cho phép ✅" : "Chưa cho phép 🚫"}
              </p>
            </div>
          </div>

          {/* Manual day adjust */}
          <div className="flex items-center gap-2">
            <p className="text-xs text-slate-500 font-semibold">Chỉnh ngày:</p>
            <input
              type="number"
              min={1} max={30}
              defaultValue={acc.day_number}
              className="w-16 text-xs border border-slate-200 rounded-lg px-2 py-1 text-center"
              onBlur={e => {
                const v = parseInt(e.target.value);
                if (v >= 1 && v <= 30 && v !== acc.day_number)
                  act(() => api.resetDay(acc.user_id, v));
              }}
            />
            <button
              onClick={() => act(() => api.resetDay(acc.user_id, 1))}
              disabled={loading}
              className="btn bg-red-50 text-red-600 hover:bg-red-100 text-xs py-1 px-2.5"
            >
              <RotateCcw className="w-3 h-3" /> Reset về ngày 1
            </button>
          </div>
        </div>
      )}

      {/* Action message */}
      {msg && (
        <div className={cn(
          "px-4 py-2 text-xs font-semibold text-center",
          msg.includes("Lỗi") || msg.includes("fail") ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
        )}>
          {msg}
        </div>
      )}

      {/* Checkpoint warning */}
      {acc.status === "checkpoint" && (
        <div className="mx-4 mb-4 flex items-start gap-2 bg-orange-50 border border-orange-200 rounded-xl px-3 py-2.5">
          <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
          <p className="text-xs text-orange-700">
            Nick đang gặp checkpoint. Cần xử lý thủ công trên AdsPower rồi nhấn <strong>"Xóa checkpoint"</strong> để tiếp tục.
          </p>
        </div>
      )}
    </div>
  );
}

export function AccountsPage() {
  const { data: accounts, loading, refetch } = useApi(api.getAccounts);
  const [filter, setFilter] = useState<"all" | "active" | "checkpoint" | "inactive">("all");

  const filtered = (accounts ?? []).filter(a =>
    filter === "all" ? true : a.status === filter
  );

  const counts = {
    all:        (accounts ?? []).length,
    active:     (accounts ?? []).filter(a => a.status === "active").length,
    checkpoint: (accounts ?? []).filter(a => a.status === "checkpoint").length,
    inactive:   (accounts ?? []).filter(a => a.status === "inactive" || a.status === "banned").length,
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Nick Manager" subtitle="Quản lý và vận hành từng tài khoản" onRefresh={refetch} refreshing={loading} />

      <div className="flex-1 overflow-y-auto p-6">
        {/* Filter tabs */}
        <div className="flex gap-2 mb-5 flex-wrap">
          {(["all", "active", "checkpoint", "inactive"] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "btn text-xs py-1.5 px-3",
                filter === f ? "btn-primary" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
            >
              {{all: "Tất cả", active: "Hoạt động", checkpoint: "Checkpoint", inactive: "Dừng/Khóa"}[f]}
              <span className={cn(
                "ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold",
                filter === f ? "bg-white/20" : "bg-slate-100"
              )}>{counts[f]}</span>
            </button>
          ))}
        </div>

        {loading ? <PageLoader /> : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filtered.map(acc => (
              <AccountCard key={acc.user_id} acc={acc} onAction={refetch} />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-2 text-center py-16 text-slate-400">
                <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="font-semibold">Không có nick nào</p>
                <p className="text-xs mt-1">Thêm account vào accounts.json</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const Users_ = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);
