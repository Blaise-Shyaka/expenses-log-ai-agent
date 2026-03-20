#standard packages

#third party packages

from pydantic import BaseModel, Field,EmailStr

#local packages


from datetime import datetime
from typing import Optional
from uuid import UUID

class CategoryBase(BaseModel):
  name: str
  description: Optional[str] = None

class CategoryCreate(CategoryBase):
  pass

class Category(CategoryBase):
  id: UUID

  class Config:
    from_attributes = True

class ExpenseBase(BaseModel):
  amount: float
  description: Optional[str] = None
  date: Optional[datetime] = Field(default_factory=datetime.now)

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
  days: Optional[int] = None
  category_name: Optional[str] = None

class UserBase(BaseModel):
  first_name:str
  last_name:str
  email:EmailStr

class UserCreate(UserBase):
  password:str|None=None

class User(UserBase):
  id:UUID