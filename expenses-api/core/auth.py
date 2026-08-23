from dataclasses import dataclass, field
from typing import Any

import jwt
from jwt import PyJWKClient

from config.db_config import app_settings

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(app_settings.AUTH_JWKS_URI, cache_keys=True)
    return _jwks_client


def verify_jwt(token: str) -> dict[str, Any]:
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)
    payload: dict[str, Any] = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=app_settings.AUTH_AUDIENCE,
        issuer=app_settings.AUTH_ISSUER,
        leeway=10,
    )
    return payload


@dataclass
class Principal:
    sub: str
    acting_user: str
    scopes: frozenset[str] = field(default_factory=lambda: frozenset[str]())
    token_type: str = "user"
    is_authenticated: bool = True
