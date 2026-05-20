const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:9122") + "/api";

// ── Netclaw ─────────────────────────────────────────────────────────────────

export interface HealthCheckLog {
  id: number;
  pc_name: string;
  health_result: string;
  created_at: string;
}

export interface TokenUsageLog {
  id: number;
  pc_name: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  usage_date: string;
}

export interface LastActiveLog {
  pc_name: string;
  last_active_at: string;
}

export interface HealthcheckStats {
  total: number;
  running: number;
  degraded: number;
  stopped: number;
  by_day: { day: string; count: number }[];
}

// ── Timesheet ────────────────────────────────────────────────────────────────

export interface TimesheetAutoLog {
  id: number;
  machine_id: string;
  ip: string;
  check_in: string | null;
  check_out: string | null;
  logged_date: string;
  status: string | null;
  received_at: string;
}

export interface TimesheetManualLog {
  id: number;
  username: string;
  check_in: string | null;
  check_out: string | null;
  office_hour_work: string | null;
  ot_work: string | null;
  logged_date: string;
  status: string;
  created_at: string;
}

export interface MergedTimesheet {
  id: number | null;
  machine_id: string | null;
  ip: string | null;
  username: string | null;
  usercode: string | null;
  name: string | null;
  department: string | null;
  hostname: string | null;
  auto_check_in: string | null;
  auto_check_out: string | null;
  onscreen_time: string | null;
  manual_check_in: string | null;
  manual_check_out: string | null;
  office_hour_work: string | null;
  ot_work: string | null;
  status: string | null;
  logged_date: string;
  received_at: string;
}

// ── Employees ────────────────────────────────────────────────────────────────

export interface Employee {
  username: string;
  name: string;
  usercode: string;
  department: string | null;
  ip: string | null;
  hostname: string | null;
  created_at: string;
}

export interface EmployeeCreate {
  username: string;
  name: string;
  usercode: string;
  department?: string | null;
  ip?: string | null;
  hostname?: string | null;
}

export interface EmployeeUpdate {
  name?: string;
  usercode?: string;
  department?: string | null;
  ip?: string | null;
  hostname?: string | null;
}

// ── HTTP helpers ─────────────────────────────────────────────────────────────

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail;
    const msg = typeof detail === "string" ? detail : (detail ? JSON.stringify(detail) : `${res.status} ${res.statusText}`);
    throw new Error(msg);
  }
  return res.json();
}

async function fetchEmpty(path: string, init?: RequestInit): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail;
    const msg = typeof detail === "string" ? detail : (detail ? JSON.stringify(detail) : `${res.status} ${res.statusText}`);
    throw new Error(msg);
  }
}

// ── API client ───────────────────────────────────────────────────────────────

export const api = {
  // Netclaw
  healthcheckStats: () => fetchJson<HealthcheckStats>("/v1/netclaw/stats"),
  healthChecks:     (limit = 100) => fetchJson<HealthCheckLog[]>(`/v1/netclaw/health-check?limit=${limit}`),
  tokenUsage:       (limit = 100) => fetchJson<TokenUsageLog[]>(`/v1/netclaw/token-usage?limit=${limit}`),
  lastActive:       () => fetchJson<LastActiveLog[]>("/v1/netclaw/last-active"),

  // Timesheet
  timesheetMerged: (limit = 1000) => fetchJson<MergedTimesheet[]>(`/v1/logs/timesheet/merged?limit=${limit}`),

  // Employees
  employees: (search?: string) =>
    fetchJson<Employee[]>(`/v1/employees${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  importEmployees: (rows: EmployeeCreate[]) =>
    fetchJson<Employee[]>("/v1/employees/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rows),
    }),
  updateEmployee: (username: string, data: EmployeeUpdate) =>
    fetchJson<Employee>(`/v1/employees/${encodeURIComponent(username)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  deleteEmployee: (username: string) =>
    fetchEmpty(`/v1/employees/${encodeURIComponent(username)}`, { method: "DELETE" }),
};
