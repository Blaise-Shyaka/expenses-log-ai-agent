from contextvars import ContextVar

acting_user_ctx: ContextVar[str | None] = ContextVar("acting_user_ctx", default=None)
