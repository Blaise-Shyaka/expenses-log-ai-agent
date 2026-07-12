import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

from src.mcp_server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp_url = os.environ.get("MCP_URL", "http://0.0.0.0:8124")
    parsed = urlparse(mcp_url)
    host = parsed.hostname or "0.0.0.0"
    port = parsed.port or 8124
    mcp.run(transport="streamable-http", host=host, port=port)  # type: ignore[call-arg]
