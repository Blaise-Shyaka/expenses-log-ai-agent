import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import Runnable

from .agent_state import ExpensesAgentState
from .context import request_timezone_ctx
from .llm import SYSTEM_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

BoundLLM = Runnable[LanguageModelInput, AIMessage]

_active_llm: BoundLLM | None = None


def set_active_llm(llm: BoundLLM) -> None:
    global _active_llm
    _active_llm = llm


LangGraphNodeOutput = dict[str, Any]


def _today_for_request() -> str:
    tz_name = request_timezone_ctx.get()
    try:
        tz = ZoneInfo(tz_name) if tz_name else ZoneInfo("UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).strftime("%A, %B %d, %Y")


def llm_node(state: ExpensesAgentState) -> LangGraphNodeOutput:
    if _active_llm is None:
        raise RuntimeError("LLM not initialized — call set_active_llm() before using llm_node")
    logger.info(f"Input state messages: {state['messages']}")
    system_message = SystemMessage(
        content=SYSTEM_PROMPT_TEMPLATE.format(today=_today_for_request())
    )
    msgs = [system_message] + state["messages"]
    logger.info(f"Messages being sent to LLM: {msgs}")
    response = _active_llm.invoke(msgs)
    return {"messages": [response]}
