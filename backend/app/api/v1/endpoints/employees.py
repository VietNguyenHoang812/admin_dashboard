from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeRead
from app.services.employee_service import (
    get_all_employees, bulk_create_employees, update_employee, delete_employee,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[EmployeeRead],
    summary="List employees",
    description=(
        "Return all employees ordered by name. "
        "Pass `search` to filter across `name`, `username`, `usercode`, `department`, `ip`, and `pc_name`."
    ),
)
async def list_employees(
    search: str | None = Query(None, description="Case-insensitive search term"),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_employees(db, search=search)


@router.post(
    "/import",
    response_model=list[EmployeeRead],
    summary="Bulk import employees",
    description=(
        "Import a list of employees in one request. "
        "`username` is the primary key — duplicate usernames return **409**. "
        "Matches the columns in `test_data/template_staff_info.xlsx`."
    ),
)
async def import_employees(rows: list[EmployeeCreate], db: AsyncSession = Depends(get_db)):
    try:
        return await bulk_create_employees(db, rows)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Duplicate username: {e.orig}")


@router.put(
    "/{username}",
    response_model=EmployeeRead,
    summary="Update employee",
    description="Partially update an employee record. Only supplied fields are changed. `username` (primary key) cannot be changed.",
)
async def edit_employee(
    username: str,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    emp = await update_employee(db, username, data)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.delete(
    "/{username}",
    status_code=204,
    summary="Delete employee",
    description="Permanently delete an employee by username. Returns **204** on success.",
)
async def remove_employee(username: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_employee(db, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
