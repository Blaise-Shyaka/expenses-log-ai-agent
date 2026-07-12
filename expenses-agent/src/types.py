# TODO: Duplicated from expenses-api/schemas/schema.py. Here's an issue to track it: https://github.com/Blaise-Shyaka/momo-expenses-langraph-ai-agent/issues/16

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: UUID

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    amount: float
    description: str | None = None
    date: datetime | None = Field(default_factory=datetime.now)


class ExpenseCreate(ExpenseBase):
    category_name: str


class Expense(ExpenseBase):
    id: UUID
    category_id: UUID

    class Config:
        from_attributes = True


class ExpenseWithCategory(Expense):
    category: Category


class CategoryWithTotal(Category):
    total_expenses: float


class ExpenseTotalResponse(BaseModel):
    total: float
    start_date: datetime
    days: int | None = None
    category_name: str | None = None
