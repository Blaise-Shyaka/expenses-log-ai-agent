import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn  # type: ignore[import-untyped]
from ag_ui_langgraph import add_langgraph_fastapi_endpoint  # type: ignore[import-untyped]
from copilotkit import LangGraphAGUIAgent  # type: ignore[import-untyped]
from fastapi import FastAPI  # type: ignore[import-untyped]
from langgraph.checkpoint.memory import MemorySaver  # type: ignore[import-untyped]
from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]
from langgraph.prebuilt import ToolNode, tools_condition  # type: ignore[import-untyped]

from src.agent_state import ExpensesAgentState
from src.llm import get_active_llm
from src.mcp_client import MCP_URL, load_tools, wait_for_mcp
from src.nodes import llm_node, set_active_llm

# The MCP server (src/mcp_server.py) runs as a separate process.
# Start it before launching this agent: uv run python -m src.mcp_server


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # type: ignore[misc]
    mcp_url = MCP_URL
    await wait_for_mcp(mcp_url)
    tools = await load_tools(mcp_url)

    bound_llm = get_active_llm(tools)
    set_active_llm(bound_llm)

    checkpointer = MemorySaver()
    graph = StateGraph(ExpensesAgentState)

    graph.add_node(llm_node)  # pyright: ignore[reportUnknownMemberType]
    graph.add_node("tools", ToolNode(tools))  # pyright: ignore[reportUnknownMemberType]

    graph.add_edge(START, "llm_node")  # pyright: ignore[reportUnknownMemberType]
    graph.add_conditional_edges("llm_node", tools_condition, {"tools": "tools", END: END})  # pyright: ignore[reportUnknownMemberType]
    graph.add_edge("tools", "llm_node")  # pyright: ignore[reportUnknownMemberType]

    chat = graph.compile(checkpointer=checkpointer)  # pyright: ignore[reportUnknownMemberType]

    add_langgraph_fastapi_endpoint(
        app,
        agent=LangGraphAGUIAgent(
            name="Reddington",
            description="AI-powered expense tracking assistant.",
            graph=chat,
        ),
        path="/",
    )

    yield


app = FastAPI(lifespan=lifespan)  # type: ignore[call-arg]


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8123)),
        reload=True,
    )


if __name__ == "__main__":
    main()
