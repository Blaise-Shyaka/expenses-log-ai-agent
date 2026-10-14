from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import BINARY

from db.base import BaseModel


class UserDB(BaseModel):
    __tablename__ = "users"

    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)


class CategoryDB(BaseModel):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_categories_user_id_name"),)

    name: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.id"), nullable=False)

    expenses: Mapped[list["ExpenseDB"]] = relationship(back_populates="category")


class ExpenseDB(BaseModel):
    __tablename__ = "expenses"

    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    category_id: Mapped[bytes | None] = mapped_column(BINARY(16), ForeignKey("categories.id"))
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.id"), nullable=False)

    category: Mapped["CategoryDB"] = relationship(back_populates="expenses")
