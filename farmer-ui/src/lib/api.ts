// ─── API client ────────────────────────────────────────────────────────────
const BASE = "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ─── Types ──────────────────────────────────────────────────────────────────
export interface Account {
  user_id: string;
  name: string;
  day_number: number;
  status: "active" | "checkpoint" | "inactive" | "banned";
  last_run: string | null;
  checkpoint_count: number;
  sessions_today: number;
  allow_seeding: boolean;
  plan_notes: string;
}

export interface DayPlan {
  day: number;
  sessions: number;
  window: string;
  allow_seeding: boolean;
  notes: string;
  actions: [string, number][];
}

export interface SessionLog {
  id: number;
  account_id: string;
  action: string;
  result: string;
  day_number: number;
  created_at: string;
}

export interface RunResult {
  success: boolean;
  message: string;
}

export interface SchedulerStatus {
  running: boolean;
  next_run: string | null;
  timezone: string;
  hour: number;
  minute: number;
}

export interface Stats {
  total_accounts: number;
  active_accounts: number;
  checkpoint_accounts: number;
  sessions_today: number;
  seeding_enabled: number;
  avg_day: number;
}

// ─── Accounts ────────────────────────────────────────────────────────────────
export const api = {
  // Dashboard
  getStats: ()                           => req<Stats>("/stats"),

  // Accounts
  getAccounts: ()                        => req<Account[]>("/accounts"),
  runAccount: (user_id: string)          => req<RunResult>(`/accounts/${user_id}/run`, { method: "POST" }),
  resetDay: (user_id: string, day: number) =>
    req<RunResult>(`/accounts/${user_id}/day`, { method: "PATCH", body: JSON.stringify({ day }) }),
  setStatus: (user_id: string, status: string) =>
    req<RunResult>(`/accounts/${user_id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),

  // Schedule
  getSchedule: ()                        => req<DayPlan[]>("/schedule"),
  getDayPlan: (day: number)              => req<DayPlan>(`/schedule/${day}`),

  // Logs
  getLogs: (limit?: number)              => req<SessionLog[]>(`/logs?limit=${limit ?? 100}`),
  getAccountLogs: (user_id: string)      => req<SessionLog[]>(`/logs/${user_id}`),

  // Scheduler daemon
  getSchedulerStatus: ()                 => req<SchedulerStatus>("/scheduler/status"),
  startScheduler: ()                     => req<RunResult>("/scheduler/start", { method: "POST" }),
  stopScheduler: ()                      => req<RunResult>("/scheduler/stop", { method: "POST" }),
  triggerNow: ()                         => req<RunResult>("/scheduler/trigger", { method: "POST" }),
};
