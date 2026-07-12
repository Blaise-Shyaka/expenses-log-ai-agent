from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_db
from core.constants import TEST_USER_ID_BYTES
from db.models import CategoryDB, ExpenseDB
from schemas.schema import (
    CategoryWithTotal,
    Expense,
    ExpenseCreate,
    ExpenseTotalResponse,
    ExpenseWithCategory,
)

router = APIRouter()


@router.post("/", response_model=Expense, tags=["Expenses"])
async def create_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    category_stmt = select(CategoryDB).where(
        func.lower(CategoryDB.name) == expense.category_name.lower()
    )
    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if not db_category:
        # TODO: Replace TEST_USER_ID_BYTES with authenticated user's ID
        db_category = CategoryDB(name=expense.category_name, user_id=TEST_USER_ID_BYTES)
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)

    # TODO: Replace TEST_USER_ID_BYTES with authenticated user's ID
    db_expense = ExpenseDB(
        amount=expense.amount,
        description=expense.description,
        date=expense.date,
        category_id=db_category.id,
        user_id=TEST_USER_ID_BYTES,
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense


@router.get("/{expense_id}", response_model=ExpenseWithCategory, tags=["Expenses"])
async def read_expense(expense_id: UUID, db: AsyncSession = Depends(get_db)):
    expense_stmt = (
        select(ExpenseDB)
        .options(selectinload(ExpenseDB.category))
        .where(ExpenseDB.id == expense_id.bytes)
    )
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
    db: AsyncSession = Depends(get_db),
):
    expense_stmt = select(ExpenseDB).options(selectinload(ExpenseDB.category))
    if category_name:
        expense_stmt = (
            expense_stmt.join(CategoryDB)
            .filter(func.lower(CategoryDB.name) == category_name.lower())
            .offset(skip)
            .limit(limit)
        )

    result = await db.execute(expense_stmt)
    return result.scalars().all()


@router.get("/totals/by-category", response_model=list[CategoryWithTotal], tags=["Reports"])
async def get_expenses_by_category(db: AsyncSession = Depends(get_db)):
    expense_by_category_stmt = (
        select(CategoryDB, func.sum(ExpenseDB.amount).label("total_expenses"))
        .join(ExpenseDB, CategoryDB.id == ExpenseDB.category_id)
        .group_by(CategoryDB.id)
    )
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
    db: AsyncSession = Depends(get_db),
):
    if days is not None and start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    elif start_date is None:
        days = 30
        start_date = datetime.now() - timedelta(days=days)

    expense_stmt = select(func.sum(ExpenseDB.amount).label("total")).where(
        ExpenseDB.date >= start_date
    )

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
