from fastapi import APIRouter
from app.api.v1.endpoints import logs, employees, auth, netclaw

router = APIRouter()
router.include_router(auth.router,     prefix="/auth",     tags=["auth"])
router.include_router(employees.router, prefix="/employees", tags=["employees"])
router.include_router(logs.router,     prefix="/logs",     tags=["logs"])
router.include_router(netclaw.router,  prefix="/netclaw",  tags=["netclaw"])
