from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CategoryDB, ExpenseDB
from db.repositories import CategoryRepository, ExpensesRepository, UsersRepository

pytestmark = pytest.mark.anyio


async def _seed(session: AsyncSession, user: UUID, name: str) -> tuple[CategoryDB, ExpenseDB]:
    await UsersRepository(session).ensure(user.bytes)
    category = await CategoryRepository(session, user.bytes).create(
        CategoryDB(name=name, user_id=user.bytes)
    )
    expense = await ExpensesRepository(session, user.bytes).create(
        ExpenseDB(amount=10.0, category_id=category.id, user_id=user.bytes)
    )
    await session.commit()
    return category, expense


async def test_categories_are_scoped_to_their_user(
    session: AsyncSession, user_a: UUID, user_b: UUID
) -> None:
    category_b, _ = await _seed(session, user_b, "food")
    repo_a = CategoryRepository(session, user_a.bytes)

    assert await repo_a.read_by_id(UUID(bytes=category_b.id)) is None
    assert await repo_a.read_by_name("FOOD") is None
    assert await repo_a.read_all() == []


async def test_expenses_are_scoped_to_their_user(
    session: AsyncSession, user_a: UUID, user_b: UUID
) -> None:
    _, expense_b = await _seed(session, user_b, "food")
    repo_a = ExpensesRepository(session, user_a.bytes)

    assert await repo_a.read_by_id(UUID(bytes=expense_b.id)) is None
    assert await repo_a.read_all() == []
    assert await repo_a.read_totals_by_category() == []


async def test_unscoped_repository_sees_every_user(
    session: AsyncSession, user_a: UUID, user_b: UUID
) -> None:
    await _seed(session, user_a, "food")
    await _seed(session, user_b, "rent")

    assert len(await CategoryRepository(session, None).read_all()) == 2


async def test_update_sets_every_field(session: AsyncSession, user_a: UUID) -> None:
    category, _ = await _seed(session, user_a, "food")
    repo = CategoryRepository(session, user_a.bytes)

    updated = await repo.update(
        {"name": "groceries", "description": "weekly"}, UUID(bytes=category.id)
    )

    assert updated is not None
    assert (updated.name, updated.description) == ("groceries", "weekly")


async def test_update_and_delete_respect_scope(
    session: AsyncSession, user_a: UUID, user_b: UUID
) -> None:
    category_b, _ = await _seed(session, user_b, "food")
    repo_a = CategoryRepository(session, user_a.bytes)
    category_id = UUID(bytes=category_b.id)

    assert await repo_a.update({"name": "stolen"}, category_id) is None
    assert await repo_a.delete(category_id) is False


async def test_delete_by_uuid(session: AsyncSession, user_a: UUID) -> None:
    _, expense = await _seed(session, user_a, "food")
    repo = ExpensesRepository(session, user_a.bytes)

    assert await repo.delete(UUID(bytes=expense.id)) is True
    assert await repo.read_by_id(UUID(bytes=expense.id)) is None
    assert await repo.delete(uuid4()) is False
