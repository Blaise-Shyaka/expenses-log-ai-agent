import logging
import os

import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
_AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "true").lower() not in ("false", "0", "no")
_AUTH_ISSUER = os.environ.get("AUTH_ISSUER", "")
_AUTH_JWKS_URI = os.environ.get("AUTH_JWKS_URI", "")

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_AUTH_JWKS_URI)
    return _jwks_client


class AuthError(Exception):
    pass


def verify_user_token(token: str) -> str:
    if not _AUTH_REQUIRED:
        logger.warning(
            "AUTH_REQUIRED=false — skipping JWT verification, using dev user id %s",
            DEV_USER_ID,
        )
        return DEV_USER_ID

    if not token:
        raise AuthError("Missing bearer token")

    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload: dict[str, object] = jwt.decode(  # type: ignore[assignment]
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="expenses-agent",
            issuer=_AUTH_ISSUER,
            leeway=10,
            options={"require": ["sub", "exp", "iss", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise AuthError("Wrong audience") from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthError("Wrong issuer") from exc
    except jwt.PyJWTError as exc:
        raise AuthError(f"Invalid token: {exc}") from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise AuthError("Token missing sub claim")
    return sub
