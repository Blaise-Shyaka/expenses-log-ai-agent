import logging
from typing import Any

from .agent_state import ExpensesAgentState
from .llm import system_message

logger = logging.getLogger(__name__)

_active_llm: Any = None


def set_active_llm(llm: Any) -> None:
    global _active_llm
    _active_llm = llm


def llm_node(state: ExpensesAgentState) -> dict[str, Any]:
    if _active_llm is None:
        raise RuntimeError("LLM not initialized — call set_active_llm() before using llm_node")
    logger.info(f"Input state messages: {state['messages']}")
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = _active_llm.invoke(msgs)
    return {"messages": [response]}
