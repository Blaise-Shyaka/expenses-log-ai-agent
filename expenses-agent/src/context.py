from contextvars import ContextVar

acting_user_ctx: ContextVar[str | None] = ContextVar("acting_user_ctx", default=None)
request_timezone_ctx: ContextVar[str | None] = ContextVar("request_timezone_ctx", default=None)
