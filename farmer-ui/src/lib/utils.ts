import { clsx, type ClassValue } from "clsx";
export const cn = (...inputs: ClassValue[]) => clsx(inputs);

export const STATUS_LABEL: Record<string, string> = {
  active:     "Hoạt động",
  checkpoint: "Checkpoint",
  inactive:   "Tạm dừng",
  banned:     "Bị khóa",
};

export const STATUS_COLOR: Record<string, string> = {
  active:     "bg-emerald-100 text-emerald-700",
  checkpoint: "bg-orange-100 text-orange-700",
  inactive:   "bg-slate-100 text-slate-600",
  banned:     "bg-red-100 text-red-700",
};

export function formatDate(iso: string | null) {
  if (!iso) return "Chưa chạy";
  const d = new Date(iso);
  return d.toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}

export function dayPhase(day: number) {
  if (day <= 7)  return { label: "Tuần 1 — Người mới",   color: "bg-blue-100 text-blue-700" };
  if (day <= 14) return { label: "Tuần 2 — Làm quen",    color: "bg-violet-100 text-violet-700" };
  if (day <= 21) return { label: "Tuần 3 — Hoà nhập",    color: "bg-amber-100 text-amber-700" };
  return           { label: "Tuần 4+ — Người thật",      color: "bg-emerald-100 text-emerald-700" };
}
