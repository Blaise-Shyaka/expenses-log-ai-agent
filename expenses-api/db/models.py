#standard packages
from datetime import datetime

#third party packages
from sqlalchemy import String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import BINARY

#local packages 
from db.base import BaseModel


class UserDB(BaseModel):
  __tablename__ = "users"

  first_name = mapped_column(String(255), nullable=False)
  last_name = mapped_column(String(255), nullable=False)
  email = mapped_column(String(255), unique=True, index=True, nullable=False)
  hashed_password = mapped_column(String(255), index=True)
  google_id = mapped_column(String(255), index=True)
  expenses=relationship("ExpenseDB",back_populates='user')
  

class CategoryDB(BaseModel):
  __tablename__ = "categories"

  name = mapped_column(String(255), unique=True, index=True)
  description = mapped_column(String(500), nullable=True)
  user_id = mapped_column(BINARY(16), ForeignKey("users.id"), nullable=False)
  expenses = relationship("ExpenseDB", back_populates="category")


class ExpenseDB(BaseModel):
  __tablename__ = "expenses"

  amount: Mapped[float] = mapped_column(Float)
  description = mapped_column(String(500), nullable=True)
  date = mapped_column(DateTime, default=datetime.now)
  category_id = mapped_column(BINARY(16), ForeignKey("categories.id"))
  user_id = mapped_column(BINARY(16), ForeignKey("users.id"), nullable=False)
  category = relationship("CategoryDB", back_populates="expenses")
  user=relationship("UserDB",back_populates='expenses')