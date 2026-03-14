from src.nodes import gemini_node
from src.agent_state import ExpensesAgentState
from src.tools import tools
from langgraph.graph import StateGraph, START, END # type: ignore - No stub file in langgraph, unfortunately. Worth keeping an eye on the langgraph repo. Maybe even contribute that.
from langgraph.prebuilt import tools_condition, ToolNode

from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = StateGraph(ExpensesAgentState)

graph.add_node(gemini_node) # type: ignore
graph.add_node("tools", ToolNode(tools)) # type: ignore

graph.add_edge(START, "gemini_node")
graph.add_conditional_edges(
    "gemini_node", tools_condition, {"tools": "tools", END: END}
)
graph.add_edge("tools", "gemini_node")

chat = graph.compile(checkpointer=checkpointer) # type: ignore
