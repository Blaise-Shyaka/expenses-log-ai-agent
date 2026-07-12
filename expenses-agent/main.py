import os

import uvicorn  # type: ignore[import-untyped]
from ag_ui_langgraph import add_langgraph_fastapi_endpoint  # type: ignore[import-untyped]
from copilotkit import LangGraphAGUIAgent  # type: ignore[import-untyped]
from fastapi import FastAPI  # type: ignore[import-untyped]
from langgraph.checkpoint.memory import MemorySaver  # type: ignore[import-untyped]
from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]
from langgraph.prebuilt import ToolNode, tools_condition  # type: ignore[import-untyped]

from src.agent_state import ExpensesAgentState
from src.nodes import llm_node
from src.tools import tools

checkpointer = MemorySaver()
graph = StateGraph(ExpensesAgentState)

graph.add_node(llm_node)  # pyright: ignore[reportUnknownMemberType]
graph.add_node("tools", ToolNode(tools))  # pyright: ignore[reportUnknownMemberType]

graph.add_edge(START, "llm_node")  # pyright: ignore[reportUnknownMemberType]
graph.add_conditional_edges("llm_node", tools_condition, {"tools": "tools", END: END})  # pyright: ignore[reportUnknownMemberType]
graph.add_edge("tools", "llm_node")  # pyright: ignore[reportUnknownMemberType]

chat = graph.compile(checkpointer=checkpointer)  # pyright: ignore[reportUnknownMemberType]

app = FastAPI()

add_langgraph_fastapi_endpoint(
    app,
    agent=LangGraphAGUIAgent(
        name="Reddington",
        description="AI-powered expense tracking assistant.",
        graph=chat,
    ),
    path="/",
)


def main() -> None:
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8123)),
        reload=True,
    )


if __name__ == "__main__":
    main()
