import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_db
from core.auth import Principal
from core.provisioning import ensure_user
from core.security import check_scope, get_principal
from db.models import CategoryDB, ExpenseDB
from schemas.schema import (
    CategoryWithTotal,
    Expense,
    ExpenseCreate,
    ExpenseTotalResponse,
    ExpenseWithCategory,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Expense, tags=["Expenses"])
async def create_expense(
    expense: ExpenseCreate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> ExpenseDB:
    check_scope(principal, "expenses:write")

    if principal.is_authenticated and principal.acting_user:
        await ensure_user(db, principal.acting_user)
        logger.info("write sub=%s acting_user=%s", principal.sub, principal.acting_user)

    user_bytes = UUID(principal.acting_user).bytes if principal.acting_user else b""

    category_stmt = select(CategoryDB).where(
        func.lower(CategoryDB.name) == expense.category_name.lower()
    )
    if principal.acting_user:
        category_stmt = category_stmt.where(CategoryDB.user_id == user_bytes)

    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if not db_category:
        db_category = CategoryDB(name=expense.category_name, user_id=user_bytes)
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)

    db_expense = ExpenseDB(
        amount=expense.amount,
        description=expense.description,
        date=expense.date,
        category_id=db_category.id,
        user_id=user_bytes,
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


@router.get("/{expense_id}", response_model=ExpenseWithCategory, tags=["Expenses"])
async def read_expense(
    expense_id: UUID,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> ExpenseDB:
    check_scope(principal, "expenses:read")

    expense_stmt = (
        select(ExpenseDB)
        .options(selectinload(ExpenseDB.category))
        .where(ExpenseDB.id == expense_id.bytes)
    )
    if principal.is_authenticated and principal.acting_user:
        expense_stmt = expense_stmt.where(ExpenseDB.user_id == UUID(principal.acting_user).bytes)

    result = await db.execute(expense_stmt)
    expense = result.scalars().first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.get("/", response_model=list[ExpenseWithCategory], tags=["Expenses"])
async def read_expenses(
    skip: int = 0,
    limit: int = 100,
    category_name: str | None = None,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> list[ExpenseDB]:
    check_scope(principal, "expenses:read")

    expense_stmt = select(ExpenseDB).options(selectinload(ExpenseDB.category))

    if principal.is_authenticated and principal.acting_user:
        expense_stmt = expense_stmt.where(ExpenseDB.user_id == UUID(principal.acting_user).bytes)

    if category_name:
        expense_stmt = (
            expense_stmt.join(CategoryDB)
            .filter(func.lower(CategoryDB.name) == category_name.lower())
            .offset(skip)
            .limit(limit)
        )

    result = await db.execute(expense_stmt)
    return list(result.scalars().all())


@router.get("/totals/by-category", response_model=list[CategoryWithTotal], tags=["Reports"])
async def get_expenses_by_category(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryWithTotal]:
    check_scope(principal, "expenses:read")

    expense_by_category_stmt = (
        select(CategoryDB, func.sum(ExpenseDB.amount).label("total_expenses"))
        .join(ExpenseDB, CategoryDB.id == ExpenseDB.category_id)
        .group_by(CategoryDB.id)
    )
    if principal.is_authenticated and principal.acting_user:
        user_bytes = UUID(principal.acting_user).bytes
        expense_by_category_stmt = expense_by_category_stmt.where(
            CategoryDB.user_id == user_bytes
        ).where(ExpenseDB.user_id == user_bytes)

    result = await db.execute(expense_by_category_stmt)
    results = result.all()

    return [
        CategoryWithTotal(
            id=category.id,
            name=category.name,
            description=category.description,
            total_expenses=total or 0.0,
        )
        for category, total in results
    ]


@router.get("/totals/since", response_model=ExpenseTotalResponse, tags=["Reports"])
async def get_expenses_since(
    days: int | None = None,
    start_date: datetime | None = None,
    category_name: str | None = None,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> ExpenseTotalResponse:
    check_scope(principal, "expenses:read")

    if days is not None and start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    elif start_date is None:
        days = 30
        start_date = datetime.now() - timedelta(days=days)

    expense_stmt = select(func.sum(ExpenseDB.amount).label("total")).where(
        ExpenseDB.date >= start_date
    )

    if principal.is_authenticated and principal.acting_user:
        expense_stmt = expense_stmt.where(ExpenseDB.user_id == UUID(principal.acting_user).bytes)

    if category_name:
        expense_stmt = expense_stmt.join(CategoryDB).filter(
            func.lower(CategoryDB.name) == category_name.lower()
        )

    result = await db.execute(expense_stmt)
    total = result.scalar() or 0.0

    return ExpenseTotalResponse(
        total=total,
        start_date=start_date,
        days=days,
        category_name=category_name,
    )
