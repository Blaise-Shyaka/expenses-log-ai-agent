import asyncio
import logging
import time
from os import environ

import httpx

logger = logging.getLogger(__name__)

_RENEW_BEFORE_EXPIRY_SECONDS = 60


class _TokenCache:
    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    def _needs_renewal(self) -> bool:
        if self._token is None:
            return True
        return time.time() >= self._expires_at - _RENEW_BEFORE_EXPIRY_SECONDS

    async def _fetch(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        audience: str,
    ) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": audience,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code == 401:
                raise RuntimeError(
                    f"client_credentials request rejected (401) from {token_url}; "
                    "check MCP_CLIENT_ID / MCP_CLIENT_SECRET"
                )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            token = data.get("access_token")
            if not isinstance(token, str) or not token:
                raise RuntimeError(
                    f"Token response from {token_url} missing 'access_token'"
                )
            expires_in = data.get("expires_in", 900)
            if not isinstance(expires_in, (int, float)):
                expires_in = 900
            self._token = token
            self._expires_at = time.time() + float(expires_in)

    async def get_token(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        audience: str,
    ) -> str:
        if not self._needs_renewal():
            assert self._token is not None
            return self._token
        async with self._lock:
            if not self._needs_renewal():
                assert self._token is not None
                return self._token
            await self._fetch(token_url, client_id, client_secret, audience)
            assert self._token is not None
            return self._token


class ServiceTokenClient:
    def __init__(self) -> None:
        self._cache = _TokenCache()

    async def build_headers(self, acting_user: str) -> dict[str, str]:
        token_url = environ.get("AUTH_TOKEN_URL", "")
        client_id = environ.get("MCP_CLIENT_ID", "")
        client_secret = environ.get("MCP_CLIENT_SECRET", "")

        if not token_url or not client_id or not client_secret:
            raise RuntimeError(
                "AUTH_TOKEN_URL, MCP_CLIENT_ID, and MCP_CLIENT_SECRET must be set "
                "for authenticated outbound calls"
            )

        token = await self._cache.get_token(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            audience="expenses-api",
        )
        return {
            "Authorization": f"Bearer {token}",
            "X-Acting-User": acting_user,
        }


svc_token_client = ServiceTokenClient()
