import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_mcp_adapters.interceptors import MCPToolCallRequest  # type: ignore[import-untyped]

from .context import acting_user_ctx
from .token_client import get_service_token

logger = logging.getLogger(__name__)

_AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "true").lower() not in ("false", "0", "no")
_DEV_USER_ID = "00000000-0000-0000-0000-000000000001"


class AuthHeaderInterceptor:
    async def __call__(  # type: ignore[misc]
        self,
        request: MCPToolCallRequest,
        handler: Callable[[MCPToolCallRequest], Awaitable[Any]],
    ) -> Any:
        svc_token = await get_service_token()
        acting_user = acting_user_ctx.get()
        if acting_user is None:
            if _AUTH_REQUIRED:
                raise RuntimeError("acting_user_ctx not set for authenticated request")
            acting_user = _DEV_USER_ID
        patched = request.override(
            headers={
                **(request.headers or {}),
                "Authorization": f"Bearer {svc_token}",
                "X-Acting-User": acting_user,
            }
        )
        return await handler(patched)
