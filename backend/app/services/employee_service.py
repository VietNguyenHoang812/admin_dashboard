from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


async def get_all_employees(db: AsyncSession, search: str | None = None) -> list[Employee]:
    q = select(Employee).order_by(Employee.name)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Employee.name.ilike(term),
                Employee.usercode.ilike(term),
                Employee.username.ilike(term),
                Employee.department.ilike(term),
                Employee.ip.ilike(term),
            )
        )
    result = await db.execute(q)
    return list(result.scalars().all())


async def bulk_create_employees(db: AsyncSession, rows: list[EmployeeCreate]) -> list[Employee]:
    employees = [
        Employee(
            name=r.name,
            usercode=r.usercode,
            username=r.username,
            department=r.department,
            ip=r.ip,
        )
        for r in rows
    ]
    db.add_all(employees)
    await db.commit()
    for e in employees:
        await db.refresh(e)
    return employees


async def update_employee(db: AsyncSession, employee_id: int, data: EmployeeUpdate) -> Employee | None:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(emp, field, value)
    await db.commit()
    await db.refresh(emp)
    return emp


async def delete_employee(db: AsyncSession, employee_id: int) -> bool:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        return False
    await db.delete(emp)
    await db.commit()
    return True
