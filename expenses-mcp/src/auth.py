"""Acting-user resolution choke-point for every MCP tool call.

Rule (per spec):
  1. Token has `act-on-behalf` scope AND X-Acting-User header present
     → acting user = header value (canonical UUID string)
  2. X-Acting-User header present WITHOUT `act-on-behalf` scope
     → raise ToolError (reject)
  3. No X-Acting-User header
     → acting user = token `sub` claim
     → fall back to token `client_id` if `sub` is absent
"""

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token, get_http_headers

_ACT_ON_BEHALF_SCOPE = "act-on-behalf"
_ACTING_USER_HEADER = "x-acting-user"


def resolve_acting_user() -> str:
    """Resolve the acting user for the current tool call.

    Reads the verified access token via get_access_token() and incoming
    HTTP headers via get_http_headers().  Must be called from within an
    active authenticated MCP request context.

    Returns:
        Canonical acting-user UUID string.

    Raises:
        ToolError: If an X-Acting-User header is supplied by a caller
                   whose token does not carry the act-on-behalf scope.
        RuntimeError: If no access token is present (should not happen
                      when AUTH_REQUIRED is true; callers may propagate).
    """
    token = get_access_token()
    if token is None:
        raise RuntimeError("resolve_acting_user() called without an authenticated token")

    scopes: list[str] = token.scopes
    has_act_on_behalf = _ACT_ON_BEHALF_SCOPE in scopes

    headers = get_http_headers(include={_ACTING_USER_HEADER})
    acting_user_header = headers.get(_ACTING_USER_HEADER)

    if acting_user_header is not None:
        if not has_act_on_behalf:
            raise ToolError(
                "Unauthorized delegation: X-Acting-User header requires the "
                f"'{_ACT_ON_BEHALF_SCOPE}' scope, which is absent from the "
                "presented token."
            )
        return acting_user_header

    sub: str | None = token.claims.get("sub")
    if sub:
        return sub
    return token.client_id
