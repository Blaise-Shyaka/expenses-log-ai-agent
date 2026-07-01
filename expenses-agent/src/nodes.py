from .llm import system_message
from .agent_state import ExpensesAgentState
from .llm import gemini_llm
import logging

logger = logging.getLogger(__name__)

def gemini_node(state: ExpensesAgentState):
    logger.info(f"Input state messages: {state['messages']}")
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = gemini_llm.invoke(msgs)
    return {"messages": [response]}
