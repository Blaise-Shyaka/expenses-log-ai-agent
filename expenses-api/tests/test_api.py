from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CategoryDB, UserDB
from db.repositories import ExpensesRepository
from exceptions.custom_exceptions import RepositoryException
from tests.conftest import ClientFactory

pytestmark = pytest.mark.anyio

EXPENSE = {"amount": 12.5, "description": "lunch", "category_name": "Food"}


async def test_create_expense_provisions_user_and_category(
    client_for: ClientFactory, session: AsyncSession, user_a: UUID
) -> None:
    response = await client_for(user_a).post("/api/v1/expenses/", json=EXPENSE)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "amount", "description", "date", "category_id"}
    assert await session.get(UserDB, user_a.bytes) is not None
    category = (await session.execute(select(CategoryDB))).scalars().one()
    assert (category.name, category.user_id) == ("Food", user_a.bytes)
    assert UUID(body["category_id"]).bytes == category.id


async def test_read_expense_returns_nested_category(
    client_for: ClientFactory, user_a: UUID
) -> None:
    client = client_for(user_a)
    created = (await client.post("/api/v1/expenses/", json=EXPENSE)).json()

    response = await client.get(f"/api/v1/expenses/{created['id']}")

    assert response.status_code == 200
    assert response.json()["category"]["name"] == "Food"


async def test_other_users_expense_is_not_found(
    client_for: ClientFactory, user_a: UUID, user_b: UUID
) -> None:
    created = (await client_for(user_b).post("/api/v1/expenses/", json=EXPENSE)).json()

    response = await client_for(user_a).get(f"/api/v1/expenses/{created['id']}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Expense not found"}


async def test_category_not_found(client_for: ClientFactory, user_a: UUID) -> None:
    client = client_for(user_a)

    by_id = await client.get(f"/api/v1/categories/{uuid4()}")
    by_name = await client.get("/api/v1/categories/name/nothing")

    assert (by_id.status_code, by_id.json()) == (404, {"detail": "Category not found"})
    assert (by_name.status_code, by_name.json()) == (404, {"detail": "Category not found"})


async def test_duplicate_category_is_rejected_per_user(
    client_for: ClientFactory, user_a: UUID, user_b: UUID
) -> None:
    category = {"name": "Rent"}
    first = await client_for(user_a).post("/api/v1/categories/", json=category)
    duplicate = await client_for(user_a).post("/api/v1/categories/", json=category)
    other_user = await client_for(user_b).post("/api/v1/categories/", json=category)

    assert (first.status_code, first.json()["name"]) == (200, "rent")
    assert (duplicate.status_code, duplicate.json()) == (400, {"detail": "Category already exists"})
    assert other_user.status_code == 200


async def test_lists_only_show_own_rows(
    client_for: ClientFactory, user_a: UUID, user_b: UUID
) -> None:
    await client_for(user_b).post("/api/v1/expenses/", json=EXPENSE)
    client = client_for(user_a)

    assert (await client.get("/api/v1/expenses/")).json() == []
    assert (await client.get("/api/v1/categories/")).json() == []
    assert (await client.get("/api/v1/expenses/totals/by-category")).json() == []


async def _list_descriptions(client: AsyncClient, **params: str | int) -> list[str]:
    response = await client.get("/api/v1/expenses/", params=params)
    assert response.status_code == 200
    return [expense["description"] for expense in response.json()]


async def test_expense_list_is_paginated_newest_first(
    client_for: ClientFactory, user_a: UUID
) -> None:
    client = client_for(user_a)
    for day, category in [(2, "Food"), (4, "Rent"), (1, "Food"), (3, "Food")]:
        expense = {
            "amount": 1.0,
            "description": f"day {day}",
            "date": f"2026-01-0{day}T12:00:00",
            "category_name": category,
        }
        await client.post("/api/v1/expenses/", json=expense)

    assert await _list_descriptions(client) == ["day 4", "day 3", "day 2", "day 1"]
    assert await _list_descriptions(client, limit=2) == ["day 4", "day 3"]
    assert await _list_descriptions(client, skip=2, limit=2) == ["day 2", "day 1"]
    assert await _list_descriptions(client, category_name="food", limit=2) == ["day 3", "day 2"]
    assert await _list_descriptions(client, category_name="food", skip=2, limit=2) == ["day 1"]


async def test_expense_pages_do_not_overlap_when_dates_tie(
    client_for: ClientFactory, user_a: UUID
) -> None:
    client = client_for(user_a)
    for name in ["a", "b", "c"]:
        expense = {**EXPENSE, "description": name, "date": "2026-01-01T12:00:00"}
        await client.post("/api/v1/expenses/", json=expense)

    pages = [await _list_descriptions(client, skip=skip, limit=1) for skip in range(3)]

    assert sorted(name for page in pages for name in page) == ["a", "b", "c"]


async def test_totals(client_for: ClientFactory, user_a: UUID) -> None:
    client = client_for(user_a)
    await client.post("/api/v1/expenses/", json=EXPENSE)
    await client.post("/api/v1/expenses/", json={**EXPENSE, "amount": 7.5})

    by_category = (await client.get("/api/v1/expenses/totals/by-category")).json()
    since = (await client.get("/api/v1/expenses/totals/since")).json()
    since_food = (
        await client.get("/api/v1/expenses/totals/since", params={"category_name": "food"})
    ).json()

    assert [(row["name"], row["total_expenses"]) for row in by_category] == [("Food", 20.0)]
    assert (since["total"], since["days"], since["category_name"]) == (20.0, 30, None)
    assert (since_food["total"], since_food["category_name"]) == (20.0, "food")


async def test_missing_scope_is_forbidden(client_for: ClientFactory, user_a: UUID) -> None:
    client = client_for(user_a, scopes=frozenset({"expenses:read"}))

    response = await client.post("/api/v1/expenses/", json=EXPENSE)

    assert response.status_code == 403


async def test_failed_expense_insert_rolls_back_new_category(
    client_for: ClientFactory,
    session: AsyncSession,
    user_a: UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_create(self: ExpensesRepository, obj: object) -> None:
        raise RepositoryException("boom")

    monkeypatch.setattr(ExpensesRepository, "create", failing_create)

    response = await client_for(user_a).post("/api/v1/expenses/", json=EXPENSE)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert (await session.execute(select(func.count()).select_from(CategoryDB))).scalar() == 0
