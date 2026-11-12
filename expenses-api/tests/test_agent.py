import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.graph import END, START, MessagesState, StateGraph  # type: ignore[import-untyped]

from agent import server
from main import app

pytestmark = pytest.mark.anyio

RUN_INPUT: dict[str, object] = {
    "threadId": "t1",
    "runId": "r1",
    "state": {},
    "messages": [],
    "tools": [],
    "context": [],
    "forwardedProps": {},
}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _noop(state: MessagesState) -> dict[str, list[Any]]:
    return {"messages": []}


def _fake_verify(token: str) -> str:
    return "user-1"


def _compiled_graph() -> Any:
    builder = StateGraph(MessagesState)
    builder.add_node("noop", _noop)  # pyright: ignore[reportUnknownMemberType]
    builder.add_edge(START, "noop")  # pyright: ignore[reportUnknownMemberType]
    builder.add_edge("noop", END)  # pyright: ignore[reportUnknownMemberType]
    return builder.compile()  # pyright: ignore[reportUnknownMemberType]


async def _wait_until(condition: Any, timeout: float = 2.0) -> None:
    async with asyncio.timeout(timeout):
        while not condition():
            await asyncio.sleep(0.01)


async def test_agent_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.post("/agent", json=RUN_INPUT)
    assert response.status_code == 401


async def test_agent_skips_api_audience_check(client: AsyncClient) -> None:
    # A user token has audience expenses-agent, which the API's own check would reject;
    # /agent must reach the agent's verifier instead of failing in enforce_auth.
    response = await client.post(
        "/agent", json=RUN_INPUT, headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token")


async def test_agent_not_ready_returns_503(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "verify_user_token", _fake_verify)
    monkeypatch.setattr(server, "_agent", None)
    response = await client.post("/agent", json=RUN_INPUT)
    assert response.status_code == 503


async def test_health_reports_agent_not_loaded(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": {"name": None}}


async def test_agent_disabled_without_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def must_not_build() -> AbstractAsyncContextManager[Any]:
        raise AssertionError("graph built with no model configured")

    async with server.agent_lifespan(must_not_build):
        await asyncio.sleep(0)
    assert server.agent_status() == {"name": None}


async def test_agent_retries_failed_startup_then_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    @asynccontextmanager
    async def flaky_graph() -> AsyncGenerator[Any]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("MCP server not ready")
        yield _compiled_graph()

    task = asyncio.create_task(server.keep_agent_running(flaky_graph, retry_delay=0.01))
    try:
        await _wait_until(lambda: server.agent_status()["name"] is not None)
        assert attempts == 2
        assert server.agent_status() == {"name": server.AGENT_NAME}
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert server.agent_status() == {"name": None}
