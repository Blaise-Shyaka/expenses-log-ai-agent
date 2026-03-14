from .llm import system_message
from .agent_state import ExpensesAgentState
from .llm import gemini_llm
from .tools import tools
import logging

logger = logging.getLogger(__name__)

tool_map = {tool.__name__: tool for tool in tools}


def gemini_node(state: ExpensesAgentState):
    logger.info(f"Input state messages: {state['messages']}")
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = gemini_llm.invoke(msgs)
    return {"messages": [response]}


# print("called", messages, state["messages"])
# return { "messages": gemini_llm.invoke(messages + state["messages"]) }
