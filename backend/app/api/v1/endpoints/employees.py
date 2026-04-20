from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.services.employee_service import (
    get_all_employees, bulk_create_employees, update_employee, delete_employee,
)

router = APIRouter()


@router.get("", response_model=list[EmployeeRead])
async def list_employees(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_employees(db, search=search)


@router.post("/import", response_model=list[EmployeeRead])
async def import_employees(rows: list[EmployeeCreate], db: AsyncSession = Depends(get_db)):
    try:
        return await bulk_create_employees(db, rows)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Duplicate usercode or username: {e.orig}")


@router.put("/{employee_id}", response_model=EmployeeRead)
async def edit_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        emp = await update_employee(db, employee_id, data)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Duplicate usercode or username: {e.orig}")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.delete("/{employee_id}", status_code=204)
async def remove_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_employee(db, employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
