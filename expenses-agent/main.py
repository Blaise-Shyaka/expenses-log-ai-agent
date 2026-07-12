import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn  # type: ignore[import-untyped]
from ag_ui_langgraph import add_langgraph_fastapi_endpoint  # type: ignore[import-untyped]
from copilotkit import LangGraphAGUIAgent  # type: ignore[import-untyped]
from fastapi import FastAPI  # type: ignore[import-untyped]

from src.graph import make_graph


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # type: ignore[misc]
    async with make_graph() as compiled:  # type: ignore[misc]
        add_langgraph_fastapi_endpoint(
            app,
            agent=LangGraphAGUIAgent(
                name="Reddington",
                description="AI-powered expense tracking assistant.",
                graph=compiled,
            ),
            path="/",
        )

        yield


app = FastAPI(lifespan=lifespan)  # type: ignore[call-arg]


def main() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8123)), reload=True)


if __name__ == "__main__":
    main()
