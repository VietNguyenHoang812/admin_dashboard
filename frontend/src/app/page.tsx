"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import * as XLSX from "xlsx";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import {
  LayoutDashboard, Users, Calendar, Monitor, Settings,
  Search, Bell, MoreHorizontal, TrendingUp, TrendingDown,
  Upload, Pencil, Trash2, X, Check,
  User, AtSign, Building2, LogIn, LogOut, PenLine, FileText, Network, ChevronDown,
  ArrowUp, ArrowDown, ChevronsUpDown, Hash, Download, RefreshCw,
} from "lucide-react";
import {
  api, HealthcheckStats, MergedTimesheet, Employee, EmployeeCreate,
  HealthCheckLog, TokenUsageLog, LastActiveLog,
} from "@/lib/api";
import { isAuthenticated, clearAuth, getUsername } from "@/lib/auth";

/* ─── helpers ─────────────────────────────────────────── */
function todayYmd() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Ho_Chi_Minh" });
}
function sevenDaysAgoYmd() {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toLocaleDateString("en-CA", { timeZone: "Asia/Ho_Chi_Minh" });
}

function fmt(iso: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
}
function fmtTime(iso: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" });
}
function pct(n: number, total: number) {
  return total ? Math.round((n / total) * 100) : 0;
}

/* ─── sidebar nav ──────────────────────────────────────── */
const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
  { icon: Monitor,         label: "Healthcheck", id: "healthcheck" },
  { icon: Calendar,        label: "Timesheet",   id: "timesheet" },
  { icon: Users,           label: "Employees",   id: "employees" },
  { icon: Settings,        label: "Settings",    id: "settings" },
];

/* ─── sparkline wave (decorative) ──────────────────────── */
function Sparkline() {
  return (
    <svg viewBox="0 0 200 50" className="w-full opacity-60" preserveAspectRatio="none">
      <path d="M0,25 C20,10 40,40 60,25 C80,10 100,40 120,25 C140,10 160,40 180,25 C190,18 195,22 200,25"
        fill="none" stroke="white" strokeWidth="2" />
      <path d="M0,35 C25,20 45,45 70,30 C95,15 115,42 140,28 C160,18 180,38 200,30"
        fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" />
    </svg>
  );
}

/* ─── date picker with DD-MM-YYYY display ───────────────── */
function DatePickerInput({ label, value, onChange, min }: {
  label: string; value: string; onChange: (v: string) => void; min?: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  const display = value ? value.split("-").reverse().join("-") : "DD-MM-YYYY";
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-zinc-400 shrink-0">{label}</span>
      <div className="relative flex items-center cursor-pointer" onClick={() => ref.current?.showPicker?.()}>
        <span className="text-sm border border-zinc-200 rounded-xl pl-3 pr-8 py-2 bg-zinc-50 text-zinc-700 w-36 font-mono select-none">
          {display}
        </span>
        <Calendar size={14} className="absolute right-3 z-10 text-zinc-400 pointer-events-none" />
        <input
          ref={ref}
          type="date"
          value={value}
          min={min}
          onChange={(e) => onChange(e.target.value)}
          className="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
        />
      </div>
    </div>
  );
}

/* ─── stat progress card ────────────────────────────────── */
function StatCard({ label, value, progress, color }: { label: string; value: number; progress: number; color: string }) {
  return (
    <div className="bg-white rounded-2xl p-4 flex items-center gap-4 shadow-sm">
      <div className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold shrink-0"
        style={{ backgroundColor: `${color}20`, color }}>
        {value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-zinc-700">{label}</p>
        <div className="mt-2 h-1.5 w-full rounded-full bg-zinc-100">
          <div className="h-1.5 rounded-full transition-all" style={{ width: `${progress}%`, backgroundColor: color }} />
        </div>
      </div>
    </div>
  );
}

type EditDraft = { name: string; usercode: string; department: string; ip: string; hostname: string };
type View = "dashboard" | "healthcheck" | "timesheet" | "employees";

/* ═══════════════════════════════════════════════════════════ */
export default function Dashboard() {
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [loggedInUser, setLoggedInUser] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    } else {
      setLoggedInUser(getUsername());
      setAuthReady(true);
    }
  }, [router]);

  const [activeView, setActiveView] = useState<View>("dashboard");
  const [stats, setStats] = useState<HealthcheckStats | null>(null);
  const [healthChecks, setHealthChecks] = useState<HealthCheckLog[]>([]);
  const [tokenUsage, setTokenUsage]     = useState<TokenUsageLog[]>([]);
  const [lastActive, setLastActive]     = useState<LastActiveLog[]>([]);
  const [timesheet, setTimesheet] = useState<MergedTimesheet[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [lastUpdated, setLastUpdated] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  /* timesheet filter + sort */
  const [dateFrom, setDateFrom] = useState(sevenDaysAgoYmd);
  const [dateTo, setDateTo]     = useState(todayYmd);
  const [deptFilter, setDeptFilter] = useState("");
  type SortCol = "name" | "username" | "usercode" | "department" | "logged_date" | "status" | "auto_check_in" | "auto_check_out" | "onscreen_time" | "manual_check_in" | "manual_check_out" | "office_hour_work" | "ot_work";
  const [sortCol, setSortCol] = useState<SortCol | null>("logged_date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  /* employee actions */
  const [empSearch, setEmpSearch] = useState("");
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft>({ name: "", usercode: "", department: "", ip: "", hostname: "" });
  const [editError, setEditError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  type EmpSortCol = "name" | "usercode" | "username" | "department" | "ip";
  const [empSortCol, setEmpSortCol] = useState<EmpSortCol | null>(null);
  const [empSortDir, setEmpSortDir] = useState<"asc" | "desc">("asc");
  const [empDeptFilter, setEmpDeptFilter] = useState("");
  type ConflictEntry = { incoming: EmployeeCreate; existing: Employee };
  const [importPending, setImportPending] = useState<{ newRows: EmployeeCreate[]; conflicts: ConflictEntry[] } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const empSearchRef = useRef(empSearch);
  useEffect(() => { empSearchRef.current = empSearch; }, [empSearch]);

  const refreshEmployees = useCallback(async (search?: string) => {
    const emp = await api.employees(search);
    setEmployees(emp);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, hc, tu, la, ts] = await Promise.all([
        api.healthcheckStats(),
        api.healthChecks(),
        api.tokenUsage(),
        api.lastActive(),
        api.timesheetMerged(),
      ]);
      setStats(s);
      setHealthChecks(hc);
      setTokenUsage(tu);
      setLastActive(la);
      setTimesheet(ts);
      setLastUpdated(new Date().toLocaleTimeString("vi-VN"));
      setError(null);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }, []);

  // Load data once on mount
  useEffect(() => { refresh(); }, [refresh]);

  // Debounced search — reads latest empSearch via ref, never stale
  useEffect(() => {
    const t = setTimeout(() => refreshEmployees(empSearchRef.current || undefined), 300);
    return () => clearTimeout(t);
  }, [empSearch, refreshEmployees]);

  function parseExcelPayload(file: File): Promise<EmployeeCreate[]> {
    return file.arrayBuffer().then((buffer) => {
      const wb = XLSX.read(buffer, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json<Record<string, string>>(ws, { defval: "" });
      return rows.map((r) => ({
        username: String(r["username"] ?? r["Username"] ?? r["Tên đăng nhập"] ?? ""),
        name: String(r["name"] ?? r["Name"] ?? r["Họ tên"] ?? ""),
        usercode: String(r["usercode"] ?? r["Usercode"] ?? r["Mã NV"] ?? ""),
        department: String(r["department"] ?? r["Department"] ?? r["Phòng ban"] ?? "") || null,
        ip: String(r["ip"] ?? r["IP"] ?? r["Địa chỉ IP"] ?? "") || null,
        hostname: String(r["hostname"] ?? r["Hostname"] ?? r["pc_name"] ?? r["PC Name"] ?? r["pc name"] ?? "") || null,
      }));
    });
  }

  async function handleFileImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportStatus("Parsing…");
    try {
      const payload = await parseExcelPayload(file);
      const conflicts: ConflictEntry[] = [];
      const newRows: EmployeeCreate[] = [];
      for (const row of payload) {
        const existing = employees.find((emp) => emp.usercode === row.usercode);
        if (existing) conflicts.push({ incoming: row, existing });
        else newRows.push(row);
      }
      if (conflicts.length > 0) {
        setImportStatus(null);
        setImportPending({ newRows, conflicts });
      } else {
        const imported = await api.importEmployees(payload);
        setImportStatus(`Imported ${imported.length} records`);
        await refreshEmployees(empSearch || undefined);
      }
    } catch (err) { setImportStatus(`Error: ${String(err)}`); }
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function confirmImport(accept: boolean) {
    if (!importPending) return;
    const { newRows, conflicts } = importPending;
    setImportPending(null);
    if (!accept) return;
    try {
      setImportStatus("Importing…");
      await Promise.all(
        conflicts.map(({ incoming, existing }) =>
          api.updateEmployee(existing.username, {
            name: incoming.name,
            usercode: incoming.usercode,
            department: incoming.department,
            ip: incoming.ip,
            hostname: incoming.hostname,
          })
        )
      );
      if (newRows.length > 0) await api.importEmployees(newRows);
      setImportStatus(`Imported ${newRows.length} new, updated ${conflicts.length} record${conflicts.length !== 1 ? "s" : ""}`);
      await refreshEmployees(empSearch || undefined);
    } catch (err) { setImportStatus(`Error: ${String(err)}`); }
  }

  function startEdit(row: Employee) {
    setEditingId(row.username);
    setEditDraft({ name: row.name, usercode: row.usercode, department: row.department ?? "", ip: row.ip ?? "", hostname: row.hostname ?? "" });
    setEditError(null);
  }
  function cancelEdit() { setEditingId(null); setEditError(null); }
  async function saveEdit(username: string) {
    try {
      await api.updateEmployee(username, { name: editDraft.name, usercode: editDraft.usercode, department: editDraft.department || null, ip: editDraft.ip || null, hostname: editDraft.hostname || null });
      setEditingId(null);
      await refreshEmployees(empSearch || undefined);
    } catch (err) { setEditError(String(err)); }
  }
  async function handleDelete(username: string) {
    setDeletingId(username);
    try { await api.deleteEmployee(username); await refreshEmployees(empSearch || undefined); }
    catch (err) { setError(String(err)); }
    finally { setDeletingId(null); }
  }

  /* derived stats */
  const total = stats?.total ?? 0;
  const running = stats?.running ?? 0;
  const degraded = stats?.degraded ?? 0;
  const stopped = stats?.stopped ?? 0;
  const donutData = [
    { name: "Running",  value: running,  color: "#10b981" },
    { name: "Degraded", value: degraded, color: "#f59e0b" },
    { name: "Stopped",  value: stopped,  color: "#ef4444" },
  ];
  const barData = stats?.by_day ?? [];

  const uniqueDepts = Array.from(new Set(timesheet.map((r) => r.department).filter(Boolean))) as string[];

  function toggleSort(col: SortCol) {
    if (sortCol === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortCol(col); setSortDir("asc"); }
  }
  function SortIcon({ col }: { col: SortCol }) {
    if (sortCol !== col) return <ChevronsUpDown size={11} className="text-zinc-300 ml-0.5" />;
    return sortDir === "asc"
      ? <ArrowUp size={11} className="text-rose-400 ml-0.5" />
      : <ArrowDown size={11} className="text-rose-400 ml-0.5" />;
  }

  const filteredTimesheet = (() => {
    let rows = timesheet.filter((r) => {
      const ymd = r.logged_date.split("-").reverse().join("-");
      return ymd >= dateFrom && ymd <= dateTo;
    });
    if (deptFilter) rows = rows.filter((r) => r.department === deptFilter);
    rows = [...rows].sort((a, b) => {
      // primary: selected column (default: logged_date desc)
      const col = sortCol ?? "logged_date";
      const dir = sortCol ? sortDir : "desc";
      const av = a[col] ?? "";
      const bv = b[col] ?? "";
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      const primary = dir === "asc" ? cmp : -cmp;
      if (primary !== 0) return primary;
      // secondary: logged_date desc (when primary is not date)
      if (col !== "logged_date") {
        const dc = (a.logged_date ?? "") < (b.logged_date ?? "") ? -1 : (a.logged_date ?? "") > (b.logged_date ?? "") ? 1 : 0;
        if (dc !== 0) return -dc;
      }
      // tertiary: username asc
      const nc = (a.username ?? "") < (b.username ?? "") ? -1 : (a.username ?? "") > (b.username ?? "") ? 1 : 0;
      return nc;
    });
    return rows;
  })();

  const uniqueEmpDepts = Array.from(new Set(employees.map((e) => e.department).filter(Boolean))) as string[];
  function toggleEmpSort(col: EmpSortCol) {
    if (empSortCol === col) setEmpSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setEmpSortCol(col); setEmpSortDir("asc"); }
  }
  function EmpSortIcon({ col }: { col: EmpSortCol }) {
    if (empSortCol !== col) return <ChevronsUpDown size={11} className="text-zinc-300 ml-0.5" />;
    return empSortDir === "asc"
      ? <ArrowUp size={11} className="text-rose-400 ml-0.5" />
      : <ArrowDown size={11} className="text-rose-400 ml-0.5" />;
  }
  const sortedEmployees = (() => {
    let rows = empDeptFilter ? employees.filter((e) => e.department === empDeptFilter) : employees;
    if (empSortCol) {
      rows = [...rows].sort((a, b) => {
        const av = a[empSortCol] ?? "";
        const bv = b[empSortCol] ?? "";
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return empSortDir === "asc" ? cmp : -cmp;
      });
    }
    return rows;
  })();

  function statusLabel(s: string | null) {
    if (s === "present") return "Đi làm";
    if (s === "upcode")  return "Làm đêm";
    if (s === "absent")  return "Nghỉ";
    return s ?? "—";
  }

  function exportTimesheet() {
    const data = filteredTimesheet.map((row, idx) => {
      const absent = row.status === "absent";
      return {
        "No.": idx + 1,
        "Name": row.name ?? "",
        "Username": row.username ?? "",
        "Usercode": row.usercode ?? "",
        "Dept": row.department ?? "",
        "Date": row.logged_date,
        "Status": statusLabel(row.status),
        "Check In": absent ? "" : (row.auto_check_in ?? ""),
        "Check Out": absent ? "" : (row.auto_check_out ?? ""),
        "OnScreen Time": absent ? "" : (row.onscreen_time ?? ""),
        "Manual In": absent ? "" : (row.manual_check_in ?? ""),
        "Manual Out": absent ? "" : (row.manual_check_out ?? ""),
        "Office Work": absent ? "" : (row.office_hour_work ?? ""),
        "OT Work": absent ? "" : (row.ot_work ?? ""),
      };
    });
    const suffix = dateFrom === dateTo ? dateFrom : `${dateFrom}_to_${dateTo}`;
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, suffix);
    XLSX.writeFile(wb, `timesheet_${suffix}.xlsx`);
  }

  function handleLogout() {
    clearAuth();
    router.replace("/login");
  }

  const inputCls = "w-full rounded-lg border border-zinc-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-rose-300";

  if (!authReady) return null;

  /* ── layout ─────────────────────────────────────────────── */
  return (
    <>
    <div className="flex h-screen overflow-hidden bg-[#f0efe9]">

      {/* ── Sidebar ── */}
      <aside className="w-16 bg-[#0f172a] flex flex-col items-center py-6 gap-2 shrink-0">
        {/* Logo */}
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-400 to-orange-400 flex items-center justify-center mb-6">
          <span className="text-white font-bold text-sm">N</span>
        </div>

        {NAV.map(({ icon: Icon, label, id }) => (
          <button
            key={id}
            title={label}
            onClick={() => id !== "settings" && setActiveView(id as View)}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
              activeView === id
                ? "bg-white/15 text-white"
                : "text-slate-500 hover:text-slate-300 hover:bg-white/8"
            }`}
          >
            <Icon size={18} />
          </button>
        ))}

        {/* Avatar + logout at bottom */}
        <div className="mt-auto flex flex-col items-center gap-2">
          <div title={loggedInUser ?? ""} className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-400 to-indigo-500 flex items-center justify-center text-white text-xs font-bold">
            {loggedInUser ? loggedInUser[0].toUpperCase() : "?"}
          </div>
          <button
            title="Logout"
            onClick={handleLogout}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 hover:text-rose-400 hover:bg-white/8 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="flex items-center justify-between px-8 py-4 shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">
              {activeView === "dashboard"   && "Overview"}
              {activeView === "healthcheck" && "Healthcheck"}
              {activeView === "timesheet"   && "Timesheet"}
              {activeView === "employees"   && "Employees"}
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">Netclaw Admin</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white rounded-xl px-3 py-2 shadow-sm w-48">
              <Search size={14} className="text-zinc-400" />
              <span className="text-sm text-zinc-400">Search…</span>
            </div>
            {error && <span className="text-xs text-red-500 max-w-xs truncate">{error}</span>}
            <button
              onClick={refresh}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl bg-white shadow-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-50 transition-colors font-medium"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              {lastUpdated ? `Updated ${lastUpdated}` : "Refresh"}
            </button>
            <div className="relative">
              <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center shadow-sm cursor-pointer">
                <Bell size={16} className="text-zinc-600" />
              </div>
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 rounded-full text-white text-[9px] flex items-center justify-center font-bold">6</span>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white shadow-sm text-sm text-zinc-600 hover:text-rose-500 hover:shadow transition-all"
            >
              <LogOut size={14} />
              <span>Sign out</span>
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8 pb-8 space-y-6">

          {/* ════ DASHBOARD ════ */}
          {activeView === "dashboard" && (
            <>
              {/* Top row: hero + donut + stat cards */}
              <div className="grid grid-cols-12 gap-5">

                {/* Hero gradient card */}
                <div className="col-span-4 rounded-3xl bg-gradient-to-br from-[#ff7c5c] to-[#e8389a] p-6 text-white flex flex-col justify-between min-h-[200px] shadow-lg shadow-rose-200">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium opacity-80">Online Machines</p>
                    <MoreHorizontal size={16} className="opacity-60" />
                  </div>
                  <div>
                    <p className="text-4xl font-bold tracking-tight mt-1">
                      {running >= 1000 ? `${(running / 1000).toFixed(1)}k` : running}
                    </p>
                    <div className="my-3">
                      <Sparkline />
                    </div>
                    <div className="flex gap-6 text-sm">
                      <div>
                        <p className="opacity-60 text-xs">Running</p>
                        <p className="font-semibold">%{pct(running, total)}</p>
                      </div>
                      <div className="border-l border-white/30 pl-6">
                        <p className="opacity-60 text-xs">Degraded</p>
                        <p className="font-semibold">%{pct(degraded, total)}</p>
                      </div>
                      <div className="border-l border-white/30 pl-6">
                        <p className="opacity-60 text-xs">Stopped</p>
                        <p className="font-semibold">%{pct(stopped, total)}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Donut card */}
                <div className="col-span-4 bg-white rounded-3xl p-6 shadow-sm flex flex-col justify-between">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm text-zinc-500 font-medium">PC Status</p>
                      <p className="text-3xl font-bold text-zinc-900 mt-1">
                        {total >= 1000 ? `${(total / 1000).toFixed(0)}k` : total}
                      </p>
                    </div>
                    <MoreHorizontal size={16} className="text-zinc-400" />
                  </div>
                  <div className="flex items-center gap-4">
                    <PieChart width={120} height={120}>
                      <Pie data={donutData} cx={55} cy={55} innerRadius={36} outerRadius={55}
                        dataKey="value" strokeWidth={0}>
                        {donutData.map((d) => <Cell key={d.name} fill={d.color} />)}
                      </Pie>
                    </PieChart>
                    <div className="space-y-2 text-sm">
                      {donutData.map((d) => (
                        <div key={d.name} className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                          <span className="text-zinc-500">{d.name}</span>
                          <span className="font-semibold text-zinc-700 ml-auto pl-4">%{pct(d.value, total)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right stat cards */}
                <div className="col-span-4 flex flex-col gap-4">
                  <StatCard label="Timesheet Records" value={timesheet.length} progress={Math.min(timesheet.length / 2, 100)} color="#e8389a" />
                  <StatCard label="Employees"         value={employees.length} progress={Math.min(employees.length * 5, 100)} color="#f59e0b" />
                  <StatCard label="Departments"
                    value={new Set(employees.map(e => e.department).filter(Boolean)).size}
                    progress={60} color="#6366f1" />
                </div>
              </div>

              {/* Bottom row: bar chart + timesheet table */}
              <div className="grid grid-cols-12 gap-5">

                {/* Bar chart */}
                <div className="col-span-4 bg-white rounded-3xl p-6 shadow-sm">
                  <div className="flex justify-between items-center mb-4">
                    <p className="font-semibold text-zinc-800">Activity (7 days)</p>
                    <MoreHorizontal size={16} className="text-zinc-400" />
                  </div>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={barData} barSize={20}>
                      <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                      <YAxis hide />
                      <Tooltip
                        contentStyle={{ borderRadius: 12, border: "none", boxShadow: "0 4px 24px rgba(0,0,0,0.1)", fontSize: 12 }}
                        cursor={{ fill: "#f1f5f9" }}
                      />
                      <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                        {barData.map((_, i) => (
                          <Cell key={i} fill={i === barData.length - 2 ? "#e8389a" : "#e2e8f0"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 pt-4 border-t border-zinc-100 flex justify-between text-sm">
                    <div>
                      <p className="text-zinc-400 text-xs">Total logs</p>
                      <p className="font-bold text-zinc-800">{total.toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-zinc-400 text-xs">Online now</p>
                      <p className="font-bold text-emerald-500">{running.toLocaleString()}</p>
                    </div>
                  </div>
                </div>

                {/* Timesheet preview */}
                <div className="col-span-8 bg-white rounded-3xl p-6 shadow-sm">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex gap-4">
                      <button className="text-sm font-semibold text-zinc-800 border-b-2 border-zinc-800 pb-1">Timesheet Activity</button>
                      <button className="text-sm text-zinc-400 pb-1" onClick={() => setActiveView("employees")}>Employees</button>
                    </div>
                    <MoreHorizontal size={16} className="text-zinc-400" />
                  </div>
                  <div className="space-y-3">
                    {timesheet.slice(0, 5).map((row, idx) => (
                      <div key={`${row.username}-${row.logged_date ?? idx}-${row.status ?? idx}`} className="flex items-center gap-3 py-2">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center shrink-0">
                          <Monitor size={15} className="text-slate-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-zinc-800 truncate">{row.name ?? row.username ?? "—"}</p>
                          <p className="text-xs text-zinc-400">{row.hostname ?? row.username ?? "—"}</p>
                        </div>
                        <span className="text-xs bg-zinc-100 text-zinc-500 px-2 py-1 rounded-lg shrink-0">{row.department ?? "—"}</span>
                        <div className="text-right shrink-0">
                          <p className="text-sm font-semibold text-zinc-700">{row.auto_check_in ?? "—"}</p>
                          <p className="text-xs text-zinc-400">→ {row.auto_check_out ?? "—"}</p>
                        </div>
                        {row.office_hour_work
                          ? <TrendingUp size={14} className="text-emerald-500 shrink-0" />
                          : <TrendingDown size={14} className="text-zinc-300 shrink-0" />}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* ════ HEALTHCHECK ════ */}
          {activeView === "healthcheck" && (() => {
            const ONLINE_MS = 5 * 60 * 1000;
            function isOnline(t: string) { return Date.now() - new Date(t).getTime() < ONLINE_MS; }
            function healthBadge(result: string) {
              const r = result.toUpperCase();
              if (r === "OK")      return "bg-emerald-50 text-emerald-600";
              if (r === "WARNING") return "bg-amber-50 text-amber-600";
              if (r === "ERROR")   return "bg-red-50 text-red-500";
              return "bg-zinc-100 text-zinc-500";
            }
            return (
              <div className="space-y-5">

                {/* ── Last Active ── */}
                <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
                  <div className="px-6 py-5 border-b border-zinc-100 flex justify-between items-center">
                    <p className="font-semibold text-zinc-800">Last Active</p>
                    <div className="flex gap-3">
                      <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                        <span className="w-2 h-2 rounded-full bg-emerald-500" />
                        Online: <span className="font-semibold text-emerald-600">{lastActive.filter(r => isOnline(r.last_active_at)).length}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                        <span className="w-2 h-2 rounded-full bg-zinc-300" />
                        Offline: <span className="font-semibold text-zinc-500">{lastActive.filter(r => !isOnline(r.last_active_at)).length}</span>
                      </div>
                    </div>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-zinc-400 uppercase tracking-wide bg-zinc-50">
                        <th className="px-6 py-3 text-center font-medium w-12">No.</th>
                        <th className="px-6 py-3 text-left font-medium">PC Name</th>
                        <th className="px-6 py-3 text-left font-medium">Status</th>
                        <th className="px-6 py-3 text-left font-medium">Last Seen</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-50">
                      {lastActive.length === 0 ? (
                        <tr><td colSpan={4} className="text-center text-zinc-400 py-10">No data yet.</td></tr>
                      ) : lastActive.map((row, idx) => (
                        <tr key={row.pc_name} className="hover:bg-zinc-50 transition-colors">
                          <td className="px-6 py-3 text-center text-zinc-400 text-xs">{idx + 1}</td>
                          <td className="px-6 py-3 font-medium text-zinc-800 font-mono text-xs">{row.pc_name}</td>
                          <td className="px-6 py-3">
                            {isOnline(row.last_active_at)
                              ? <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />Online</span>
                              : <span className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-400"><span className="w-1.5 h-1.5 rounded-full bg-zinc-300" />Offline</span>}
                          </td>
                          <td className="px-6 py-3 text-zinc-400 text-xs">{fmt(row.last_active_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* ── Health Checks ── */}
                <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
                  <div className="px-6 py-5 border-b border-zinc-100">
                    <p className="font-semibold text-zinc-800">Health Checks</p>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-zinc-400 uppercase tracking-wide bg-zinc-50">
                        <th className="px-6 py-3 text-center font-medium w-12">No.</th>
                        <th className="px-6 py-3 text-left font-medium">PC Name</th>
                        <th className="px-6 py-3 text-left font-medium">Result</th>
                        <th className="px-6 py-3 text-left font-medium">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-50">
                      {healthChecks.length === 0 ? (
                        <tr><td colSpan={4} className="text-center text-zinc-400 py-10">No data yet.</td></tr>
                      ) : healthChecks.map((row, idx) => (
                        <tr key={row.id} className="hover:bg-zinc-50 transition-colors">
                          <td className="px-6 py-3 text-center text-zinc-400 text-xs">{idx + 1}</td>
                          <td className="px-6 py-3 font-medium text-zinc-800 font-mono text-xs">{row.pc_name}</td>
                          <td className="px-6 py-3">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${healthBadge(row.health_result)}`}>
                              {row.health_result}
                            </span>
                          </td>
                          <td className="px-6 py-3 text-zinc-400 text-xs">{fmt(row.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* ── Token Usage ── */}
                <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
                  <div className="px-6 py-5 border-b border-zinc-100">
                    <p className="font-semibold text-zinc-800">Token Usage</p>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-zinc-400 uppercase tracking-wide bg-zinc-50">
                        <th className="px-6 py-3 text-center font-medium w-12">No.</th>
                        <th className="px-6 py-3 text-left font-medium">PC Name</th>
                        <th className="px-6 py-3 text-right font-medium">Input</th>
                        <th className="px-6 py-3 text-right font-medium">Output</th>
                        <th className="px-6 py-3 text-right font-medium">Total</th>
                        <th className="px-6 py-3 text-left font-medium">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-50">
                      {tokenUsage.length === 0 ? (
                        <tr><td colSpan={6} className="text-center text-zinc-400 py-10">No data yet.</td></tr>
                      ) : tokenUsage.map((row, idx) => (
                        <tr key={row.id} className="hover:bg-zinc-50 transition-colors">
                          <td className="px-6 py-3 text-center text-zinc-400 text-xs">{idx + 1}</td>
                          <td className="px-6 py-3 font-medium text-zinc-800 font-mono text-xs">{row.pc_name}</td>
                          <td className="px-6 py-3 text-right text-zinc-600 tabular-nums">{row.input_tokens.toLocaleString()}</td>
                          <td className="px-6 py-3 text-right text-zinc-600 tabular-nums">{row.output_tokens.toLocaleString()}</td>
                          <td className="px-6 py-3 text-right font-semibold text-zinc-800 tabular-nums">{row.total_tokens.toLocaleString()}</td>
                          <td className="px-6 py-3 text-zinc-400 text-xs">{row.usage_date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

              </div>
            );
          })()}

          {/* ════ TIMESHEET ════ */}
          {activeView === "timesheet" && (
            <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
              <div className="px-6 py-5 border-b border-zinc-100 flex items-center justify-between gap-4">
                <div>
                  <p className="font-semibold text-zinc-800">Timesheet</p>
                  <p className="text-xs text-zinc-400 mt-0.5">Timesheet của CBNV</p>
                </div>
                <div className="flex items-center gap-2">
                  <DatePickerInput
                    label="Từ"
                    value={dateFrom}
                    onChange={(v) => { setDateFrom(v); if (v > dateTo) setDateTo(v); }}
                  />
                  <span className="text-zinc-400 text-xs">—</span>
                  <DatePickerInput
                    label="Đến"
                    value={dateTo}
                    min={dateFrom}
                    onChange={setDateTo}
                  />
                  <button
                    onClick={() => { const t = todayYmd(); setDateFrom(t); setDateTo(t); }}
                    className="text-xs px-3 py-2 rounded-xl bg-zinc-100 text-zinc-500 hover:bg-zinc-200 transition-colors font-medium"
                  >
                    Today
                  </button>
                  <button
                    onClick={() => { setDateFrom(sevenDaysAgoYmd()); setDateTo(todayYmd()); }}
                    className="text-xs px-3 py-2 rounded-xl bg-zinc-100 text-zinc-500 hover:bg-zinc-200 transition-colors font-medium"
                  >
                    Last 7 days
                  </button>
                  <div className="w-px h-6 bg-zinc-200 mx-1" />
                  <button
                    onClick={exportTimesheet}
                    className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-400 text-white text-sm font-medium px-4 py-2 rounded-xl shadow-sm hover:opacity-90 transition-opacity"
                  >
                    <Download size={14} />
                    Export
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-zinc-400 uppercase tracking-wide bg-zinc-50">
                      <th className="px-5 py-3 text-center font-medium w-12">No.</th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("name")}>
                        <span className="flex items-center gap-1"><User size={12} />Name<SortIcon col="name" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("username")}>
                        <span className="flex items-center gap-1"><AtSign size={12} />Username<SortIcon col="username" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("usercode")}>
                        <span className="flex items-center gap-1"><Hash size={12} />Usercode<SortIcon col="usercode" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium">
                        <div className="flex flex-col gap-1">
                          <button className="flex items-center gap-1 cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("department")}>
                            <Building2 size={12} /><span>Dept</span><SortIcon col="department" />
                          </button>
                          <select
                            value={deptFilter}
                            onChange={(e) => setDeptFilter(e.target.value)}
                            className="text-xs bg-white border border-zinc-200 rounded-md px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-rose-300 cursor-pointer normal-case font-normal text-zinc-500 w-full"
                          >
                            <option value="">All</option>
                            {uniqueDepts.map((d) => <option key={d} value={d}>{d}</option>)}
                          </select>
                        </div>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("logged_date")}>
                        <span className="flex items-center gap-1"><Calendar size={12} />Date<SortIcon col="logged_date" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("status")}>
                        <span className="flex items-center gap-1"><Check size={12} />Status<SortIcon col="status" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("auto_check_in")}>
                        <span className="flex items-center gap-1"><LogIn size={12} />Check In<SortIcon col="auto_check_in" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("auto_check_out")}>
                        <span className="flex items-center gap-1"><LogOut size={12} />Check Out<SortIcon col="auto_check_out" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("onscreen_time")}>
                        <span className="flex items-center gap-1"><Monitor size={12} />OnScreen<SortIcon col="onscreen_time" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("manual_check_in")}>
                        <span className="flex items-center gap-1"><PenLine size={12} />Manual In<SortIcon col="manual_check_in" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("manual_check_out")}>
                        <span className="flex items-center gap-1"><PenLine size={12} />Manual Out<SortIcon col="manual_check_out" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("office_hour_work")}>
                        <span className="flex items-center gap-1"><FileText size={12} />Office Work<SortIcon col="office_hour_work" /></span>
                      </th>
                      <th className="px-5 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleSort("ot_work")}>
                        <span className="flex items-center gap-1"><FileText size={12} />OT Work<SortIcon col="ot_work" /></span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {filteredTimesheet.map((row, idx) => {
                      const absent = row.status === "absent";
                      return (
                        <tr key={`${row.username}-${row.logged_date ?? idx}-${row.status ?? idx}`} className={`hover:bg-zinc-50 transition-colors ${absent ? "opacity-60" : ""}`}>
                          <td className="px-5 py-3 text-center text-zinc-400 text-xs">{idx + 1}</td>
                          <td className="px-5 py-3 font-medium text-zinc-800">{row.name ?? "—"}</td>
                          <td className="px-5 py-3 text-zinc-600">{row.username ?? "—"}</td>
                          <td className="px-5 py-3 text-zinc-400 font-mono text-xs">{row.usercode ?? "—"}</td>
                          <td className="px-5 py-3">
                            {row.department
                              ? <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{row.department}</span>
                              : <span className="text-zinc-300">—</span>}
                          </td>
                          <td className="px-5 py-3 text-zinc-500 text-xs font-mono whitespace-nowrap">{row.logged_date}</td>
                          <td className="px-5 py-3">
                            {row.status === "present" && <span className="text-xs font-medium bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">Đi làm</span>}
                            {row.status === "upcode"  && <span className="text-xs font-medium bg-violet-50 text-violet-600 px-2 py-0.5 rounded-full">Làm đêm</span>}
                            {row.status === "absent"  && <span className="text-xs font-medium bg-red-50 text-red-500 px-2 py-0.5 rounded-full">Nghỉ</span>}
                            {!row.status && <span className="text-zinc-300">—</span>}
                          </td>
                          <td className="px-5 py-3 text-zinc-600 text-xs">{absent ? "—" : (row.auto_check_in ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-600 text-xs">{absent ? "—" : (row.auto_check_out ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-600 text-xs font-mono">{absent ? "—" : (row.onscreen_time ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-600 text-xs">{absent ? "—" : (row.manual_check_in ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-600 text-xs">{absent ? "—" : (row.manual_check_out ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-500 text-xs max-w-[180px] truncate">{absent ? "—" : (row.office_hour_work ?? "—")}</td>
                          <td className="px-5 py-3 text-zinc-500 text-xs max-w-[180px] truncate">{absent ? "—" : (row.ot_work ?? "—")}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════ EMPLOYEES ════ */}
          {activeView === "employees" && (
            <div className="bg-white rounded-3xl shadow-sm overflow-hidden">
              <div className="px-6 py-5 border-b border-zinc-100 flex items-center justify-between gap-4">
                <div>
                  <p className="font-semibold text-zinc-800">Employee Directory</p>
                  <p className="text-xs text-zinc-400 mt-0.5">{employees.length} records</p>
                </div>
                <div className="flex items-center gap-3 flex-1 max-w-md">
                  <div className="flex items-center gap-2 bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 flex-1">
                    <Search size={14} className="text-zinc-400 shrink-0" />
                    <input
                      type="text"
                      placeholder="Filter by name, username, department…"
                      value={empSearch}
                      onChange={(e) => setEmpSearch(e.target.value)}
                      className="text-sm bg-transparent outline-none w-full text-zinc-700 placeholder:text-zinc-400"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {importStatus && (
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${importStatus.startsWith("Error") ? "bg-red-50 text-red-500" : "bg-emerald-50 text-emerald-600"}`}>
                      {importStatus}
                    </span>
                  )}
                  <input ref={fileInputRef} type="file" accept=".xlsx,.xls" className="hidden" onChange={handleFileImport} />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 bg-gradient-to-r from-rose-500 to-orange-400 text-white text-sm font-medium px-4 py-2 rounded-xl shadow-sm hover:opacity-90 transition-opacity"
                  >
                    <Upload size={14} />
                    Import XLSX
                  </button>
                </div>
              </div>
              {editError && <div className="px-6 py-2 bg-red-50 text-red-600 text-sm">{editError}</div>}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-zinc-400 uppercase tracking-wide bg-zinc-50">
                      <th className="px-6 py-3 text-center font-medium w-12">No.</th>
                      <th className="px-6 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleEmpSort("name")}>
                        <span className="flex items-center gap-1"><User size={12} />Name<EmpSortIcon col="name" /></span>
                      </th>
                      <th className="px-6 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleEmpSort("usercode")}>
                        <span className="flex items-center gap-1"><Hash size={12} />Usercode<EmpSortIcon col="usercode" /></span>
                      </th>
                      <th className="px-6 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleEmpSort("username")}>
                        <span className="flex items-center gap-1"><AtSign size={12} />Username<EmpSortIcon col="username" /></span>
                      </th>
                      <th className="px-6 py-3 text-left font-medium">
                        <div className="flex items-center gap-1">
                          <button className="flex items-center gap-1 cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleEmpSort("department")}>
                            <Building2 size={12} /><span>Department</span><EmpSortIcon col="department" />
                          </button>
                          <select
                            value={empDeptFilter}
                            onChange={(e) => setEmpDeptFilter(e.target.value)}
                            className="ml-1 text-xs bg-white border border-zinc-200 rounded-md px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-rose-300 cursor-pointer normal-case font-normal text-zinc-500"
                          >
                            <option value="">All</option>
                            {uniqueEmpDepts.map((d) => <option key={d} value={d}>{d}</option>)}
                          </select>
                          <ChevronDown size={10} className="text-zinc-300 -ml-1" />
                        </div>
                      </th>
                      <th className="px-6 py-3 text-left font-medium cursor-pointer select-none hover:text-zinc-600" onClick={() => toggleEmpSort("ip")}>
                        <span className="flex items-center gap-1"><Network size={12} />IP<EmpSortIcon col="ip" /></span>
                      </th>
                      <th className="px-6 py-3 text-left font-medium">
                        <span className="flex items-center gap-1"><Monitor size={12} />Hostname</span>
                      </th>
                      <th className="px-6 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {sortedEmployees.length === 0 ? (
                      <tr><td colSpan={8} className="text-center text-zinc-400 py-12">
                        {empSearch || empDeptFilter ? "No results match your filter." : "No employees yet. Import an XLSX file to get started."}
                      </td></tr>
                    ) : sortedEmployees.map((row, idx) => editingId === row.username ? (
                      <tr key={row.username} className="bg-rose-50/40">
                        <td className="px-6 py-2 text-center text-zinc-400 text-xs">{idx + 1}</td>
                        <td className="px-6 py-2"><input className={inputCls} value={editDraft.name} onChange={(e) => setEditDraft((d) => ({ ...d, name: e.target.value }))} /></td>
                        <td className="px-6 py-2"><input className={inputCls} value={editDraft.usercode} onChange={(e) => setEditDraft((d) => ({ ...d, usercode: e.target.value }))} /></td>
                        <td className="px-6 py-2 text-zinc-400 font-mono text-xs">{row.username}</td>
                        <td className="px-6 py-2"><input className={inputCls} value={editDraft.department} onChange={(e) => setEditDraft((d) => ({ ...d, department: e.target.value }))} /></td>
                        <td className="px-6 py-2"><input className={inputCls} value={editDraft.ip} onChange={(e) => setEditDraft((d) => ({ ...d, ip: e.target.value }))} /></td>
                        <td className="px-6 py-2"><input className={inputCls} value={editDraft.hostname} onChange={(e) => setEditDraft((d) => ({ ...d, hostname: e.target.value }))} /></td>
                        <td className="px-6 py-2">
                          <div className="flex justify-end gap-2">
                            <button onClick={() => saveEdit(row.username)} className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center hover:bg-emerald-600"><Check size={14} /></button>
                            <button onClick={cancelEdit} className="w-8 h-8 rounded-lg bg-zinc-200 text-zinc-600 flex items-center justify-center hover:bg-zinc-300"><X size={14} /></button>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      <tr key={row.username} className="hover:bg-zinc-50 transition-colors">
                        <td className="px-6 py-3 text-center text-zinc-400 text-xs">{idx + 1}</td>
                        <td className="px-6 py-3 font-medium text-zinc-800">{row.name}</td>
                        <td className="px-6 py-3 text-zinc-400 font-mono text-xs">{row.usercode}</td>
                        <td className="px-6 py-3 text-zinc-600">{row.username}</td>
                        <td className="px-6 py-3">
                          {row.department
                            ? <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{row.department}</span>
                            : <span className="text-zinc-300">—</span>}
                        </td>
                        <td className="px-6 py-3 text-zinc-400 font-mono text-xs">{row.ip ?? "—"}</td>
                        <td className="px-6 py-3 text-zinc-400 font-mono text-xs">{row.hostname ?? "—"}</td>
                        <td className="px-6 py-3">
                          <div className="flex justify-end gap-2">
                            <button onClick={() => startEdit(row)} className="w-8 h-8 rounded-lg bg-zinc-100 text-zinc-500 flex items-center justify-center hover:bg-zinc-200 transition-colors"><Pencil size={13} /></button>
                            <button
                              disabled={deletingId === row.username}
                              onClick={() => { if (confirm(`Delete ${row.name}?`)) handleDelete(row.username); }}
                              className="w-8 h-8 rounded-lg bg-red-50 text-red-400 flex items-center justify-center hover:bg-red-100 transition-colors disabled:opacity-40"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>

    {/* ════ IMPORT CONFLICT DIALOG ════ */}
    {importPending && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
          <div className="px-6 py-5 border-b border-zinc-100">
            <p className="font-semibold text-zinc-800 text-base">Overwrite existing employees?</p>
            <p className="text-sm text-zinc-500 mt-1">
              {importPending.conflicts.length} employee{importPending.conflicts.length !== 1 ? "s" : ""} in this file already exist (same employee code).
              Accepting will overwrite their data.
              {importPending.newRows.length > 0 && ` ${importPending.newRows.length} new record${importPending.newRows.length !== 1 ? "s" : ""} will also be added.`}
            </p>
          </div>
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-zinc-50">
                <tr className="text-xs text-zinc-400 uppercase tracking-wide">
                  <th className="px-5 py-3 text-left font-medium">Usercode</th>
                  <th className="px-5 py-3 text-left font-medium">Current name</th>
                  <th className="px-5 py-3 text-left font-medium">New name</th>
                  <th className="px-5 py-3 text-left font-medium">Department</th>
                  <th className="px-5 py-3 text-left font-medium">IP</th>
                  <th className="px-5 py-3 text-left font-medium">Hostname</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {importPending.conflicts.map(({ incoming, existing }) => (
                  <tr key={existing.username} className="hover:bg-amber-50/40">
                    <td className="px-5 py-3 font-mono text-xs text-zinc-500">{existing.usercode}</td>
                    <td className="px-5 py-3 text-zinc-400 line-through text-xs">{existing.name}</td>
                    <td className="px-5 py-3 font-medium text-zinc-800">{incoming.name}</td>
                    <td className="px-5 py-3 text-zinc-500 text-xs">{incoming.department ?? "—"}</td>
                    <td className="px-5 py-3 font-mono text-zinc-400 text-xs">{incoming.ip ?? "—"}</td>
                    <td className="px-5 py-3 font-mono text-zinc-400 text-xs">{incoming.hostname ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t border-zinc-100 flex justify-end gap-3">
            <button
              onClick={() => confirmImport(false)}
              className="px-4 py-2 text-sm font-medium text-zinc-600 bg-zinc-100 rounded-xl hover:bg-zinc-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => confirmImport(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-rose-500 to-orange-400 rounded-xl hover:opacity-90 transition-opacity shadow-sm"
            >
              Accept & Overwrite
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}
