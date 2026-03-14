from src.nodes import gemini_node
from src.agent_state import ExpensesAgentState
from src.tools import tools
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode

from langgraph.checkpoint.memory import MemorySaver

print("in main")

checkpointer = MemorySaver()
graph = StateGraph(ExpensesAgentState)

graph.add_node(gemini_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "gemini_node")
graph.add_conditional_edges(
    "gemini_node",
    tools_condition,
    {
        "tools": "tools",  # Path to tools if needed
        END: END           # Path to end if no tools needed
    }
)
graph.add_edge("tools", "gemini_node")
# graph.add_edge("gemini_node", END)

chat = graph.compile(checkpointer=checkpointer)
