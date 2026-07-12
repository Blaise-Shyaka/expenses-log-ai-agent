from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore[import-untyped]
from langgraph.checkpoint.memory import MemorySaver  # type: ignore[import-untyped]
from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]
from langgraph.graph.state import CompiledStateGraph  # type: ignore[import-untyped]
from langgraph.prebuilt import ToolNode, tools_condition  # type: ignore[import-untyped]

from .agent_state import ExpensesAgentState
from .llm import get_active_llm
from .mcp_client import MCP_URL, wait_for_mcp
from .nodes import llm_node, set_active_llm


@asynccontextmanager
async def make_graph() -> AsyncGenerator[CompiledStateGraph]:  # type: ignore[type-arg]
    """
    Async factory for the LangGraph agent graph.

    Used by both:
    - `langgraph dev` (pointed to via langgraph.json)
    - FastAPI lifespan (imported directly in main.py)
    """
    await wait_for_mcp(MCP_URL)

    client = MultiServerMCPClient(  # type: ignore[call-arg]
        {
            "expenses": {
                "transport": "streamable_http",
                "url": f"{MCP_URL}/mcp",
            }
        }
    )
    tools = await client.get_tools()

    bound_llm = get_active_llm(tools)
    set_active_llm(bound_llm)

    checkpointer = MemorySaver()
    builder = StateGraph(ExpensesAgentState)

    builder.add_node(llm_node)  # pyright: ignore[reportUnknownMemberType]
    builder.add_node("tools", ToolNode(tools))  # pyright: ignore[reportUnknownMemberType]

    builder.add_edge(START, "llm_node")  # pyright: ignore[reportUnknownMemberType]
    builder.add_conditional_edges(  # pyright: ignore[reportUnknownMemberType]
        "llm_node", tools_condition, {"tools": "tools", END: END}
    )
    builder.add_edge("tools", "llm_node")  # pyright: ignore[reportUnknownMemberType]

    compiled = builder.compile(checkpointer=checkpointer)  # pyright: ignore[reportUnknownMemberType]

    yield compiled
