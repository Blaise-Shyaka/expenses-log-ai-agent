from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CategoryBase(BaseModel):
  name: str
  description: Optional[str] = None

class CategoryCreate(CategoryBase):
  pass

class Category(CategoryBase):
  id: int

  class Config:
    from_attributes = True

class ExpenseBase(BaseModel):
  amount: float
  description: Optional[str] = None
  date: Optional[datetime] = Field(default_factory=datetime.now)

class ExpenseCreate(ExpenseBase):
  category_name: str

class Expense(ExpenseBase):
  id: int
  category_id: int

  class Config:
    from_attributes = True

class ExpenseWithCategory(Expense):
  category: Category

class CategoryWithTotal(Category):
  total_expenses: float

class ExpenseSince(BaseModel):
  days: Optional[int]
  start_date: Optional[datetime]
  category_name: Optional[str]
