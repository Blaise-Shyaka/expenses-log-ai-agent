import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

from collections.abc import AsyncIterator, Callable
from uuid import UUID, uuid4

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from api.deps import get_db
from core.auth import Principal
from core.security import enforce_auth, get_principal
from db.base import BaseModel
from main import app

ALL_SCOPES = frozenset({"expenses:read", "expenses:write"})


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture
def user_a() -> UUID:
    return uuid4()


@pytest.fixture
def user_b() -> UUID:
    return uuid4()


type ClientFactory = Callable[..., AsyncClient]


@pytest.fixture
async def client_for(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[ClientFactory]:
    """Build an API client acting as the given user, with the given token scopes."""

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def no_auth() -> None:
        return None

    async def override_get_principal(request: Request) -> Principal:
        user = request.headers["X-Test-User"]
        scopes = frozenset(request.headers["X-Test-Scopes"].split())
        return Principal(sub=user, acting_user=user, scopes=scopes)

    clients: list[AsyncClient] = []

    def make(user: UUID, scopes: frozenset[str] = ALL_SCOPES) -> AsyncClient:
        client = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Test-User": str(user), "X-Test-Scopes": " ".join(scopes)},
        )
        clients.append(client)
        return client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[enforce_auth] = no_auth
    app.dependency_overrides[get_principal] = override_get_principal
    yield make
    app.dependency_overrides.clear()
    for client in clients:
        await client.aclose()
