# standard packages
from typing import List, Optional
from datetime import datetime
from uuid import UUID

#third party packages
from fastapi import APIRouter, Depends

#local packages 
from schemas import Expense, ExpenseCreate, ExpenseWithCategory, CategoryWithTotal, ExpenseTotalResponse
from api.deps import get_expenses_service
from services import ExpensesServices

router = APIRouter()


@router.post("/", response_model=Expense, tags=["Expenses"])
async def create_expense(expense: ExpenseCreate, expenses_service:ExpensesServices=Depends(get_expenses_service)):

     db_expense=await expenses_service.create_expense(expense=expense)
     return db_expense
     
@router.get("/",response_model=List[Expense], tags=["Expenses"])
async def read_expenses(
        skip: int = 0,
        limit: int = 100,
        category_name: Optional[str] = None,
        expenses_service:ExpensesServices=Depends(get_expenses_service)
):
    expenses=await expenses_service.read_expenses(skip=skip,limit=limit,category_name=category_name)
    return expenses


@router.get("/{expense_id}", response_model=ExpenseWithCategory, tags=["Expenses"])
async def read_expense(expense_id: UUID, expenses_service:ExpensesServices=Depends(get_expenses_service)):
    return await expenses_service.read_by_id(id=expense_id)



@router.get("/totals/by-category",response_model=List[CategoryWithTotal], tags=["Reports"])
async def get_expenses_by_category(category_name:str|None=None,expense_services:ExpensesServices=Depends(get_expenses_service)):
    results= await expense_services.read_totals_by_category(category_name=category_name)
    return results
  
@router.get("/totals/since", response_model=ExpenseTotalResponse, tags=["Reports"])
async def get_expenses_since(
        days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        category_name: Optional[str] = None,
        expenses_service:ExpensesServices=Depends(get_expenses_service)
):
      result=await expenses_service.read_totals_since(days=days,start_date=start_date,category_name=category_name)
      return result
