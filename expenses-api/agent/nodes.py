import logging
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import Runnable

from agent.agent_state import ExpensesAgentState
from agent.context import request_timezone_ctx
from agent.llm import SYSTEM_PROMPT_TEMPLATE

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


def _count_roles(messages: Sequence[BaseMessage]) -> str:
    """Count messages by role, e.g. "system=1 human=2 ai=1 tool=1". Never their content."""
    return " ".join(f"{role}={n}" for role, n in Counter(m.type for m in messages).items())


def llm_node(state: ExpensesAgentState) -> LangGraphNodeOutput:
    if _active_llm is None:
        raise RuntimeError("LLM not initialized — call set_active_llm() before using llm_node")
    system_message = SystemMessage(
        content=SYSTEM_PROMPT_TEMPLATE.format(today=_today_for_request())
    )
    msgs = [system_message] + state["messages"]
    logger.info("Calling the model with %d messages (%s)", len(msgs), _count_roles(msgs))
    response = _active_llm.invoke(msgs)
    return {"messages": [response]}
