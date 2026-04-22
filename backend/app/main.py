from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import engine, Base
import app.models.log       # noqa: F401  (registers HealthCheck, TokenUsage, LastActive, Timesheet*)
import app.models.employee  # noqa: F401

_DESCRIPTION = """
Admin Dashboard API for Viettel's internal infrastructure monitoring.

Background agents running on company PCs push system data to this API.
The frontend consumes these endpoints to visualize live status and generate reports.

## Authentication
Use `POST /api/v1/auth/login` to obtain a JWT bearer token (valid 8 hours).

## Interactive docs
- **Swagger UI**: [`/docs`](/docs)
- **ReDoc**: [`/redoc`](/redoc)
- **OpenAPI JSON**: [`/openapi.json`](/openapi.json)
"""

_TAGS_METADATA = [
    {"name": "auth",      "description": "Login and JWT token issuance."},
    {"name": "employees", "description": "Employee directory: list, import, update, delete."},
    {"name": "netclaw",   "description": "Netclaw agent data: health checks, token usage, last-active heartbeats."},
    {"name": "logs",      "description": "Timesheet logs from PC agents (auto and manual)."},
    {"name": "health",    "description": "Service health check."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Admin Dashboard API",
    version="1.0.0",
    description=_DESCRIPTION,
    openapi_tags=_TAGS_METADATA,
    contact={
        "name": "Viettel Infrastructure Team",
        "email": "admin@viettel.com.vn",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"], summary="Service health check")
async def health():
    return {"status": "ok", "environment": settings.environment}
