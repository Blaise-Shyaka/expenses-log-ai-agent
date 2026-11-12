import asyncio
import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

_AGENT_CLIENT_ID = os.environ.get("AGENT_CLIENT_ID", "")
_AGENT_CLIENT_SECRET = os.environ.get("AGENT_CLIENT_SECRET", "")
_AUTH_TOKEN_URL = os.environ.get("AUTH_TOKEN_URL", "")
_RENEWAL_BUFFER_SECONDS = 60.0

_cache_lock = asyncio.Lock()
_cached_token: str | None = None
_token_expires_at: float = 0.0


async def get_service_token() -> str:
    global _cached_token, _token_expires_at

    async with _cache_lock:
        if _cached_token and time.monotonic() < _token_expires_at - _RENEWAL_BUFFER_SECONDS:
            return _cached_token

        token, expires_in = await _fetch_token()
        _cached_token = token
        _token_expires_at = time.monotonic() + expires_in
        return _cached_token


async def _fetch_token() -> tuple[str, float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _AUTH_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": _AGENT_CLIENT_ID,
                "client_secret": _AGENT_CLIENT_SECRET,
                "audience": "expenses-mcp",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        response.raise_for_status()
        body: dict[str, object] = response.json()  # type: ignore[assignment]
        access_token = body.get("access_token")
        expires_in = body.get("expires_in", 3600)
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("Auth service returned no access_token")
        if not isinstance(expires_in, (int, float)):
            expires_in = 3600
        return access_token, float(expires_in)
