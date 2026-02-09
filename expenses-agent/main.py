from src.nodes import gemini_node
from src.agent_state import ExpensesAgentState
from src.tools import tools
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

graph = StateGraph(ExpensesAgentState)

graph.add_node(gemini_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "gemini_node")
graph.add_conditional_edges(
    "gemini_node",
    tools_condition,
    {
        "tools": "tools",  # If tools are needed, go to tools node
        "__end__": END,  # If no tools needed, end the graph
    },
)
graph.add_edge("tools", "gemini_node")
graph.compile()
