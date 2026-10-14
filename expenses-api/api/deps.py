from collections.abc import AsyncIterator, Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import Principal
from core.security import get_principal
from db.repositories import CategoryRepository, ExpensesRepository, UsersRepository
from db.session import SessionLocal
from db.unit_of_work import UnitOfWork
from services import CategoryServices, ExpensesServices


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


def get_user_scope(principal: Principal = Depends(get_principal)) -> bytes | None:
    """The acting user's id as stored in the database; None when auth is disabled."""
    return UUID(principal.acting_user).bytes if principal.acting_user else None


def get_repo[R: (CategoryRepository, ExpensesRepository)](
    cls: type[R],
) -> Callable[[AsyncSession, bytes | None], R]:
    def _get_repo(
        session: AsyncSession = Depends(get_db),
        user_id: bytes | None = Depends(get_user_scope),
    ) -> R:
        return cls(session=session, user_id=user_id)

    return _get_repo


def get_users_repo(session: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(session=session)


def get_unit_of_work(session: AsyncSession = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(session=session)


def get_category_service(
    category_repo: CategoryRepository = Depends(get_repo(CategoryRepository)),
    users_repo: UsersRepository = Depends(get_users_repo),
    uow: UnitOfWork = Depends(get_unit_of_work),
    user_id: bytes | None = Depends(get_user_scope),
) -> CategoryServices:
    return CategoryServices(
        category_repo=category_repo, users_repo=users_repo, uow=uow, user_id=user_id
    )


def get_expenses_service(
    category_repo: CategoryRepository = Depends(get_repo(CategoryRepository)),
    expenses_repo: ExpensesRepository = Depends(get_repo(ExpensesRepository)),
    users_repo: UsersRepository = Depends(get_users_repo),
    uow: UnitOfWork = Depends(get_unit_of_work),
    user_id: bytes | None = Depends(get_user_scope),
) -> ExpensesServices:
    return ExpensesServices(
        category_repo=category_repo,
        expenses_repo=expenses_repo,
        users_repo=users_repo,
        uow=uow,
        user_id=user_id,
    )
