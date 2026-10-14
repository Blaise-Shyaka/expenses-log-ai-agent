import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import BaseModel
from exceptions.custom_exceptions import RepositoryException

logger = logging.getLogger(__name__)


class GenericRepository[T: BaseModel](ABC):
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def read_all(self, skip: int = 0, limit: int = 10) -> Sequence[T]:
        raise NotImplementedError

    @abstractmethod
    async def read_by_id(self, id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, obj: dict[str, Any], id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, obj: T) -> T:
        raise NotImplementedError


class GenericSqlRepository[T: BaseModel](GenericRepository[T]):
    """SQL repository. It only flushes; committing is the caller's unit of work."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    def _scoped(self, statement: Select[tuple[T]]) -> Select[tuple[T]]:
        """Hook for subclasses to restrict queries, e.g. to the acting user's rows."""
        return statement

    async def delete(self, id: UUID) -> bool:
        db_obj = await self.read_by_id(id)
        if db_obj is None:
            return False
        try:
            await self.session.delete(db_obj)
            await self.session.flush()
        except SQLAlchemyError as exc:
            self.handle_exception("delete", exc)
        return True

    async def read_all(self, skip: int = 0, limit: int = 10) -> Sequence[T]:
        statement = self._scoped(select(self.model)).offset(skip).limit(limit)
        try:
            results = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_all", exc)
        return results.scalars().all()

    async def read_by_id(self, id: UUID) -> T | None:
        statement = self._scoped(select(self.model).where(self.model.id == id.bytes))
        try:
            results = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            self.handle_exception("read_by_id", exc)
        return results.scalars().first()

    async def update(self, obj: dict[str, Any], id: UUID) -> T | None:
        db_obj = await self.read_by_id(id)
        if db_obj is None:
            return None
        for key, value in obj.items():
            if key.startswith("_"):
                continue
            setattr(db_obj, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(db_obj)
        except SQLAlchemyError as exc:
            self.handle_exception("update", exc)
        return db_obj

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        try:
            await self.session.flush()
            await self.session.refresh(obj)
        except SQLAlchemyError as exc:
            self.handle_exception("create", exc)
        return obj

    def handle_exception(self, operation: str, exc: Exception) -> NoReturn:
        logger.error(
            "Repository exception during %s on %s: %s",
            operation,
            self.model.__name__,
            exc,
            exc_info=True,
        )
        raise RepositoryException(f"Repository error during {operation}") from exc
