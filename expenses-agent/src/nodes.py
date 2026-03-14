from langchain_core.messages import HumanMessage, SystemMessage
from .agent_state import ExpensesAgentState
from .llm import gemini_llm
from .tools import tools
import logging

logger = logging.getLogger(__name__)

tool_map = {tool.__name__: tool for tool in tools}


def gemini_node(state: ExpensesAgentState):
    is_first_turn = len(state["messages"]) == 1 and isinstance(
        state["messages"][0], HumanMessage
    )
    if is_first_turn:
        system_msg = SystemMessage(
            content="You are an AI assistant tasked with being an expenses tracker for users. Your name is Reddington. You have a friendly, helpful, playful, and respectful tone."
        )
        msgs = [system_msg] + state["messages"]
    else:
        msgs = state["messages"]
    response = gemini_llm.invoke(msgs)
    return {"messages": [response]}


# print("called", messages, state["messages"])
# return { "messages": gemini_llm.invoke(messages + state["messages"]) }
