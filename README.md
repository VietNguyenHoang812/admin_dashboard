# Admin Dashboard

A monitoring and analytics dashboard for internal infrastructure. Background agents running on company PCs push logs to the backend. The frontend visualizes this data in real time and supports exporting reports.

---

## Features

### Log Ingestion (Backend)
- [x] Receive healthcheck logs from PC agents (`POST /api/v1/logs/healthcheck`) — PC health status, active services, last ping
- [x] Receive machine timesheet logs (`POST /api/v1/logs/timesheet`) — check-in/check-out records per machine
- [x] Receive manual timesheet logs (`POST /api/v1/logs/timesheet/manual`) — user-submitted work logs with content
- [x] Merged timesheet view (`GET /api/v1/logs/timesheet/merged`) — joins machine + manual logs via IP → employee → username
- [x] Healthcheck stats (`GET /api/v1/logs/healthcheck/stats`) — running/degraded/stopped counts + 7-day activity

### Employee Management (Backend + Frontend)
- [x] Employee table — name, usercode, username, department, IP; unique constraints on usercode and username
- [x] List employees with server-side search (`GET /api/v1/employees?search=...`)
- [x] Bulk import from XLSX (`POST /api/v1/employees/import`)
- [x] Edit employee inline in table (`PUT /api/v1/employees/{id}`)
- [x] Delete employee (`DELETE /api/v1/employees/{id}`)

### Dashboard (Frontend)
- [x] Dark sidebar + cream background UI with Nunito font
- [x] Gradient hero card — online machine count with sparkline
- [x] Donut chart — PC status breakdown (Running / Degraded / Stopped)
- [x] Bar chart — 7-day healthcheck activity
- [x] Stat cards — timesheet records, employee count, department count
- [x] Real-time updates — stats and timesheet refresh every 5 seconds
- [x] Vietnam timezone — all timestamps displayed in Asia/Ho_Chi_Minh

### Timesheet View
- [x] Merged table — machine check-in/out + manual check-in/out + work content in one row
- [x] Date filter — defaults to today (Asia/Ho_Chi_Minh); change or reset with "Today" button
- [x] Department filter — dropdown in column header to filter by department
- [x] Column sort — click any column header (except No.) to sort asc/desc
- [x] Column icons — each column has a descriptive icon

### Employees View
- [x] Search — debounced filter by name, username, usercode, department, IP
- [x] Import XLSX — parse and bulk-insert from spreadsheet file
- [x] Inline edit/delete with confirmation

### Reporting
- [x] Export PC metrics as CSV (`GET /api/v1/reports/export/csv?hostname=X`)

### PC Agent Registration
- [x] PC agents register and send heartbeats (`POST /api/v1/agents/register`)
- [x] Agents push CPU, memory, and disk metrics (`POST /api/v1/metrics/ingest`)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (TypeScript, App Router) |
| Frontend UI | shadcn/ui, Tailwind CSS |
| Backend API | FastAPI (Python, async) |
| Database | PostgreSQL (SQLAlchemy async + asyncpg) |
| Message Queue | Redis |
| Package Manager | pnpm |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
admin_dashboard/
├── frontend/                        # Next.js dashboard
│   └── src/
│       ├── app/page.tsx             # Main dashboard page
│       ├── components/ui/           # shadcn/ui components
│       └── lib/api.ts               # API client
├── backend/                         # FastAPI server
│   └── app/
│       ├── api/v1/endpoints/        # agents, metrics, logs, reports
│       ├── models/                  # SQLAlchemy ORM models
│       ├── schemas/                 # Pydantic request/response schemas
│       ├── services/                # Business logic
│       └── core/                   # config, database
├── mock_agent/                      # Simulated PC agent for testing
│   ├── agent.py                     # Pushes mock logs every 5s
│   └── mock_data/                   # Sample log payloads
└── docker-compose.yml               # PostgreSQL + Redis + backend + mock agent
```

---

## Getting Started

### Prerequisites
- Docker + Docker Compose
- Node.js 20+ and pnpm
- Python 3.10+

### 1. Start backend services

```bash
cp backend/.env.example backend/.env
docker compose up -d
```

This starts PostgreSQL, Redis, the FastAPI backend, and the mock agent.

### 2. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. (Optional) Run backend without Docker

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## API Reference
****
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/agents/register` | Register or heartbeat a PC agent |
| POST | `/api/v1/metrics/ingest` | Ingest CPU/memory/disk metrics |
| GET | `/api/v1/metrics/{hostname}` | Fetch recent metrics for a PC |
| POST | `/api/v1/logs/healthcheck` | Ingest a healthcheck log |
| GET | `/api/v1/logs/healthcheck` | List recent healthcheck logs |
| POST | `/api/v1/logs/timesheet` | Ingest a machine timesheet log |
| GET | `/api/v1/logs/timesheet` | List recent machine timesheet logs |
| POST | `/api/v1/logs/timesheet/manual` | Ingest a manual user timesheet log |
| GET | `/api/v1/logs/timesheet/manual` | List recent manual timesheet logs |
| GET | `/api/v1/reports/export/csv` | Export metrics as CSV (`?hostname=X`) |
| GET | `/health` | Health check |

Interactive API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Mock Agent

A simulated PC agent (`mock_agent/`) pushes all 3 log types every 5 seconds to test the full pipeline without real PCs. It runs automatically as a Docker service.

On startup it fetches the employee list from the backend and uses real usercodes/IPs as machine identities. Falls back to hardcoded data if the backend is unavailable. Reloads staff every ~5 minutes.

---

## Commands

```bash
pnpm dev          # Start frontend dev server
pnpm build        # Production build
pnpm lint         # Lint frontend code
docker compose up -d          # Start all backend services
docker compose logs -f        # Stream logs from all services
docker compose down           # Stop all services
```
