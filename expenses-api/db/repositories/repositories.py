from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Row, Select, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import CategoryDB, ExpenseDB, UserDB

from .base_repository import GenericSqlRepository


class CategoryRepository(GenericSqlRepository[CategoryDB]):
    """Categories, restricted to `user_id` when one is given (None means unscoped)."""

    def __init__(self, session: AsyncSession, user_id: bytes | None) -> None:
        super().__init__(session=session, model=CategoryDB)
        self.user_id = user_id

    def _scoped(self, statement: Select[tuple[CategoryDB]]) -> Select[tuple[CategoryDB]]:
        if self.user_id is None:
            return statement
        return statement.where(CategoryDB.user_id == self.user_id)

    async def read_by_name(self, name: str) -> CategoryDB | None:
        statement = self._scoped(
            select(CategoryDB).where(func.lower(CategoryDB.name) == name.lower())
        )
        try:
            results = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_by_name", exc)
        return results.scalars().first()


class ExpensesRepository(GenericSqlRepository[ExpenseDB]):
    """Expenses, restricted to `user_id` when one is given (None means unscoped)."""

    def __init__(self, session: AsyncSession, user_id: bytes | None) -> None:
        super().__init__(session=session, model=ExpenseDB)
        self.user_id = user_id

    def _scoped(self, statement: Select[tuple[ExpenseDB]]) -> Select[tuple[ExpenseDB]]:
        statement = statement.options(selectinload(ExpenseDB.category))
        if self.user_id is None:
            return statement
        return statement.where(ExpenseDB.user_id == self.user_id)

    async def read_all(
        self, skip: int = 0, limit: int = 10, category_name: str | None = None
    ) -> Sequence[ExpenseDB]:
        statement = self._scoped(select(ExpenseDB))
        # Pagination only applies to the category-filtered listing, matching the
        # endpoint's behaviour before the repository refactor.
        if category_name:
            statement = (
                statement.join(CategoryDB)
                .filter(func.lower(CategoryDB.name) == category_name.lower())
                .offset(skip)
                .limit(limit)
            )
        try:
            results = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_all", exc)
        return results.scalars().all()

    async def read_totals_by_category(self) -> Sequence[Row[tuple[CategoryDB, Any]]]:
        statement = (
            select(CategoryDB, func.sum(ExpenseDB.amount).label("total_expenses"))
            .join(ExpenseDB, CategoryDB.id == ExpenseDB.category_id)
            .group_by(CategoryDB.id)
        )
        if self.user_id is not None:
            statement = statement.where(CategoryDB.user_id == self.user_id).where(
                ExpenseDB.user_id == self.user_id
            )
        try:
            results = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_totals_by_category", exc)
        return results.all()

    async def read_totals_since(self, start_date: datetime, category_name: str | None) -> float:
        statement = select(func.sum(ExpenseDB.amount).label("total")).where(
            ExpenseDB.date >= start_date
        )
        if self.user_id is not None:
            statement = statement.where(ExpenseDB.user_id == self.user_id)
        if category_name:
            statement = statement.join(CategoryDB).filter(
                func.lower(CategoryDB.name) == category_name.lower()
            )
        try:
            result = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_totals_since", exc)
        return result.scalar() or 0.0


class UsersRepository(GenericSqlRepository[UserDB]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=UserDB)

    async def ensure(self, user_id: bytes) -> None:
        """Provision the user row on first write, since identities live in the IdP."""
        try:
            existing = await self.session.get(UserDB, user_id)
        except SQLAlchemyError as exc:
            self.handle_exception("ensure", exc)
        if existing is None:
            await self.create(UserDB(id=user_id))
