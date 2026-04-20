from fastapi import APIRouter
from app.api.v1.endpoints import agents, metrics, reports, logs, employees, auth

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(logs.router, prefix="/logs", tags=["logs"])
router.include_router(employees.router, prefix="/employees", tags=["employees"])
