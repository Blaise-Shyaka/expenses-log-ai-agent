import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn  # type: ignore[import-untyped]
from ag_ui.core.types import RunAgentInput  # type: ignore[import-untyped]
from ag_ui.encoder import EventEncoder  # type: ignore[import-untyped]
from copilotkit import LangGraphAGUIAgent  # type: ignore[import-untyped]
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.auth import AuthError, verify_user_token
from src.context import acting_user_ctx
from src.graph import make_graph

_agent: LangGraphAGUIAgent | None = None  # type: ignore[misc]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # type: ignore[misc]
    global _agent
    async with make_graph() as compiled:  # type: ignore[misc]
        _agent = LangGraphAGUIAgent(
            name="Reddington",
            description="AI-powered expense tracking assistant.",
            graph=compiled,
        )
        yield


app = FastAPI(lifespan=lifespan)  # type: ignore[call-arg]


@app.post("/")
async def agent_endpoint(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    try:
        user_id = verify_user_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    input_data.thread_id = f"{user_id}:{input_data.thread_id}"
    input_data.forwarded_props = {**(input_data.forwarded_props or {}), "acting_user_id": user_id}

    accept_header = request.headers.get("accept") or ""
    encoder = EventEncoder(accept=accept_header)

    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")

    agent = _agent

    async def event_generator() -> AsyncGenerator[str]:  # type: ignore[type-arg]
        token_var = acting_user_ctx.set(user_id)
        try:
            async for event in agent.run(input_data):  # type: ignore[misc]
                yield encoder.encode(event)  # type: ignore[arg-type]
        finally:
            acting_user_ctx.reset(token_var)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())


@app.get("/health")
def health() -> dict[str, object]:
    agent = _agent
    return {
        "status": "ok",
        "agent": {"name": agent.name if agent else None},
    }


def main() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8123)), reload=True)


if __name__ == "__main__":
    main()
