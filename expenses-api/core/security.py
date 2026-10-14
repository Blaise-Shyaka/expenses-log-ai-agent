from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.db_config import app_settings
from core.auth import Principal, verify_jwt

bearer_scheme = HTTPBearer(auto_error=False)


async def enforce_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> None:
    if request.url.path == "/health":
        return
    if not app_settings.AUTH_REQUIRED:
        return
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        claims = verify_jwt(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    setattr(request.state, "jwt_claims", claims)


async def get_principal(
    request: Request,
    x_acting_user: Annotated[str | None, Header(alias="X-Acting-User")] = None,
) -> Principal:
    raw: Any = getattr(request.state, "jwt_claims", None)
    if raw is None:
        return Principal(sub="", acting_user="", is_authenticated=False)

    claims: dict[str, Any] = raw
    sub: str = str(claims.get("sub", ""))
    scope_str: str = str(claims.get("scope", ""))
    scopes: frozenset[str] = frozenset(scope_str.split())
    token_type: str = str(claims.get("token_type", "user"))

    if x_acting_user is not None:
        if "act-on-behalf" not in scopes:
            raise HTTPException(
                status_code=403,
                detail="Token lacks act-on-behalf scope to delegate acting user",
            )
        acting_user = x_acting_user
    else:
        acting_user = sub

    return Principal(sub=sub, acting_user=acting_user, scopes=scopes, token_type=token_type)


def check_scope(principal: Principal, scope: str) -> None:
    if not principal.is_authenticated:
        return
    if scope not in principal.scopes:
        raise HTTPException(status_code=403, detail=f"Missing required scope: {scope}")
