import logging
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from api.deps import get_expenses_service
from core.auth import Principal
from core.security import check_scope, get_principal
from db.models import ExpenseDB
from schemas import (
    CategoryWithTotal,
    Expense,
    ExpenseCreate,
    ExpenseTotalResponse,
    ExpenseWithCategory,
)
from services import ExpensesServices

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Expense, tags=["Expenses"])
async def create_expense(
    expense: ExpenseCreate,
    principal: Principal = Depends(get_principal),
    expenses_service: ExpensesServices = Depends(get_expenses_service),
) -> ExpenseDB:
    check_scope(principal, "expenses:write")
    if principal.is_authenticated and principal.acting_user:
        logger.info("write sub=%s acting_user=%s", principal.sub, principal.acting_user)
    return await expenses_service.create_expense(expense=expense)


@router.get("/{expense_id}", response_model=ExpenseWithCategory, tags=["Expenses"])
async def read_expense(
    expense_id: UUID,
    principal: Principal = Depends(get_principal),
    expenses_service: ExpensesServices = Depends(get_expenses_service),
) -> ExpenseDB:
    check_scope(principal, "expenses:read")
    return await expenses_service.read_by_id(id=expense_id)


@router.get("/", response_model=list[ExpenseWithCategory], tags=["Expenses"])
async def read_expenses(
    skip: int = 0,
    limit: int = 100,
    category_name: str | None = None,
    principal: Principal = Depends(get_principal),
    expenses_service: ExpensesServices = Depends(get_expenses_service),
) -> Sequence[ExpenseDB]:
    check_scope(principal, "expenses:read")
    return await expenses_service.read_expenses(skip=skip, limit=limit, category_name=category_name)


@router.get("/totals/by-category", response_model=list[CategoryWithTotal], tags=["Reports"])
async def get_expenses_by_category(
    principal: Principal = Depends(get_principal),
    expenses_service: ExpensesServices = Depends(get_expenses_service),
) -> list[CategoryWithTotal]:
    check_scope(principal, "expenses:read")
    return await expenses_service.read_totals_by_category()


@router.get("/totals/since", response_model=ExpenseTotalResponse, tags=["Reports"])
async def get_expenses_since(
    days: int | None = None,
    start_date: datetime | None = None,
    category_name: str | None = None,
    principal: Principal = Depends(get_principal),
    expenses_service: ExpensesServices = Depends(get_expenses_service),
) -> ExpenseTotalResponse:
    check_scope(principal, "expenses:read")
    return await expenses_service.read_totals_since(
        days=days, start_date=start_date, category_name=category_name
    )
