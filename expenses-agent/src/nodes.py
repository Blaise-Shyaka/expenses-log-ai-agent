import logging
from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from .agent_state import ExpensesAgentState
from .llm import system_message

logger = logging.getLogger(__name__)

BoundLLM = Runnable[LanguageModelInput, AIMessage]

_active_llm: BoundLLM | None = None


def set_active_llm(llm: BoundLLM) -> None:
    global _active_llm
    _active_llm = llm


LangGraphNodeOutput = dict[str, Any]


def llm_node(state: ExpensesAgentState) -> LangGraphNodeOutput:
    if _active_llm is None:
        raise RuntimeError("LLM not initialized — call set_active_llm() before using llm_node")
    logger.info(f"Input state messages: {state['messages']}")
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = _active_llm.invoke(msgs)
    return {"messages": [response]}
