from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import BINARY
from db.base import BaseModel
from datetime import datetime

class UserDB(BaseModel):
  __tablename__ = "users"

  first_name = Column(String(255), nullable=False)
  last_name = Column(String(255), nullable=False)
  email = Column(String(255), unique=True, index=True, nullable=False)
  hashed_password = Column(String(255), index=True)
  google_id = Column(String(255), index=True)

class CategoryDB(BaseModel):
  __tablename__ = "categories"

  name = Column(String(255), unique=True, index=True)
  description = Column(String(500), nullable=True)
  user_id = Column(BINARY(16), ForeignKey("users.id"), nullable=False)

  expenses = relationship("ExpenseDB", back_populates="category")


class ExpenseDB(BaseModel):
  __tablename__ = "expenses"

  amount: Mapped[float] = mapped_column(Float)
  description = Column(String(500), nullable=True)
  date = Column(DateTime, default=datetime.now)
  category_id = Column(BINARY(16), ForeignKey("categories.id"))
  user_id = Column(BINARY(16), ForeignKey("users.id"), nullable=False)

  category = relationship("CategoryDB", back_populates="expenses")