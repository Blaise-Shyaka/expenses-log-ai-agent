import asyncio
import os

import httpx
from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_URL: str = os.environ.get("MCP_URL", "http://localhost:8124")


async def wait_for_mcp(
    url: str,
    max_retries: int = 10,
    base_delay: float = 1.0,
) -> None:
    delay = base_delay
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            if attempt < max_retries - 1:
                await asyncio.sleep(min(delay, 30.0))
                delay *= 2
    raise RuntimeError(f"MCP server at {url} did not become healthy after {max_retries} retries")


async def load_tools(mcp_url: str) -> list[BaseTool]:
    async with MultiServerMCPClient(  # type: ignore[call-arg]
        {
            "expenses": {
                "transport": "streamable_http",
                "url": f"{mcp_url}/mcp",
            }
        }
    ) as client:
        return await client.get_tools()
