import logging

from .agent_state import ExpensesAgentState
from .llm import active_llm, system_message

logger = logging.getLogger(__name__)


def llm_node(state: ExpensesAgentState):
    logger.info(f"Input state messages: {state['messages']}")
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = active_llm.invoke(msgs)
    return {"messages": [response]}
