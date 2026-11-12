import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress
from typing import Any

from ag_ui.core.types import RunAgentInput  # type: ignore[import-untyped]
from ag_ui.encoder import EventEncoder  # type: ignore[import-untyped]
from copilotkit import LangGraphAGUIAgent  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from agent.auth import AuthError, verify_user_token
from agent.context import acting_user_ctx, request_timezone_ctx

logger = logging.getLogger(__name__)

AGENT_NAME = "Reddington"
RETRY_DELAY_SECONDS = 30.0

type GraphFactory = Callable[[], AbstractAsyncContextManager[Any]]

router = APIRouter()

_agent: LangGraphAGUIAgent | None = None  # type: ignore[misc]


def model_configured() -> bool:
    """True when there is a model to call: OLLAMA_URL or DEEPSEEK_API_KEY has a value."""
    return bool(
        os.environ.get("OLLAMA_URL", "").strip() or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    )


def _default_graph_factory() -> AbstractAsyncContextManager[Any]:
    # Imported here so a bad model setting (e.g. LLM_REQUESTS_PER_SECOND) stops the agent,
    # not the REST API.
    from agent.graph import make_graph

    return make_graph()  # type: ignore[misc]


async def keep_agent_running(
    graph_factory: GraphFactory = _default_graph_factory,
    retry_delay: float = RETRY_DELAY_SECONDS,
) -> None:
    """Build the graph and keep it loaded until cancelled, retrying if startup fails.

    The agent needs the MCP server and a service token from expenses-auth to load its
    tools. Until it has them, `/agent` answers 503 and the REST API keeps serving.
    """
    global _agent
    while True:
        try:
            async with graph_factory() as compiled:
                _agent = LangGraphAGUIAgent(
                    name=AGENT_NAME,
                    description="AI-powered expense tracking assistant.",
                    graph=compiled,
                )
                logger.warning("Agent ready")
                await asyncio.Event().wait()
        except Exception as exc:
            logger.warning(
                "Agent failed to start (%s: %s); retrying in %.0fs",
                type(exc).__name__,
                exc,
                retry_delay,
            )
        finally:
            _agent = None
        await asyncio.sleep(retry_delay)


@asynccontextmanager
async def agent_lifespan(
    graph_factory: GraphFactory = _default_graph_factory,
) -> AsyncGenerator[None]:
    """Load the agent in the background for the life of the app.

    Startup never blocks or fails the app: with no model configured the agent stays off,
    and otherwise it retries in the background while the REST API serves.
    """
    if not model_configured():
        logger.warning("Agent disabled: set OLLAMA_URL or DEEPSEEK_API_KEY to enable /agent")
        yield
        return

    task = asyncio.create_task(keep_agent_running(graph_factory))
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def agent_status() -> dict[str, object]:
    agent = _agent
    return {"name": agent.name if agent else None}  # type: ignore[misc]


@router.post("/agent")
async def agent_endpoint(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    try:
        user_id = verify_user_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    input_data.thread_id = f"{user_id}:{input_data.thread_id}"
    input_data.forwarded_props = {**(input_data.forwarded_props or {}), "acting_user_id": user_id}
    raw_timezone = (input_data.forwarded_props or {}).get("timezone")  # type: ignore[misc]
    timezone = raw_timezone if isinstance(raw_timezone, str) else None

    accept_header = request.headers.get("accept") or ""
    encoder = EventEncoder(accept=accept_header)

    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")

    agent = _agent

    async def event_generator() -> AsyncGenerator[str]:  # type: ignore[type-arg]
        user_token = acting_user_ctx.set(user_id)
        tz_token = request_timezone_ctx.set(timezone)
        try:
            async for event in agent.run(input_data):  # type: ignore[misc]
                yield encoder.encode(event)  # type: ignore[arg-type]
        finally:
            acting_user_ctx.reset(user_token)
            request_timezone_ctx.reset(tz_token)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
