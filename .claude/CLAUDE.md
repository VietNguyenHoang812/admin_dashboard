# Admin Dashboard

## Project Overview
A monitoring and analytics dashboard for Viettel's internal infrastructure. Background agents running on company PCs push system data to the backend. The frontend visualizes this data in real time and supports exporting reports.

**Key flows:**
1. **Data ingestion** — background jobs on each PC push metrics/status to the backend API
2. **Storage** — backend persists and aggregates the incoming data
3. **Visualization** — frontend displays insights and live status of all monitored PCs
4. **Reporting** — users can export data/reports from the dashboard

## Tech Stack
- **Frontend**: Next.js (TypeScript, App Router)
- **Frontend UI**: **shadcn**/ui, Tailwind CSS
- **Backend API**: FastAPI (Python, async)
- **Database**: PostgreSQL (via SQLAlchemy async + asyncpg)
- **Message Queue**: Redis (BullMQ)
- **Package manager**: pnpm

## Getting Started

```bash
# Start all services (PostgreSQL, Redis, backend)
docker compose up -d

# Frontend dev server
cd frontend && pnpm install && pnpm dev

# Backend dev server (without Docker)
cd backend && pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Project Structure
```
admin_dashboard/
├── frontend/                  # Next.js dashboard (visualization, reports)
│   └── src/app/               # App Router pages
├── backend/                   # FastAPI server
│   └── app/
│       ├── api/v1/endpoints/  # agents.py, metrics.py, reports.py
│       ├── models/            # SQLAlchemy ORM models
│       ├── schemas/           # Pydantic schemas
│       ├── services/          # Business logic
│       └── core/              # config.py, database.py
└── docker-compose.yml         # PostgreSQL + Redis + backend
```

## API Endpoints
- `POST /api/v1/agents/register` — PC agent registers/heartbeats
- `POST /api/v1/metrics/ingest` — PC agent pushes metrics
- `GET  /api/v1/metrics/{hostname}` — fetch recent metrics for a PC
- `GET  /api/v1/reports/export/csv?hostname=X` — export metrics as CSV
- `GET  /health` — health check

## Development Guidelines
- Follow existing code style and conventions.
- Write clear, descriptive commit messages.
- Test changes before submitting.
- Backend endpoints that receive agent data must be resilient to missing/partial payloads.
- Always run app after building.
- After adding any features, update in docs folder, in approriate file.

## Commands
- `pnpm dev` — start frontend dev server
- `pnpm build` — production build
- `pnpm test` — run tests
- `pnpm lint` — lint code
- `docker compose up -d` — start backend services
