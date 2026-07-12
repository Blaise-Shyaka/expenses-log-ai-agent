import os

from dotenv import load_dotenv

load_dotenv()

from src.mcp_server import mcp  # noqa: E402

if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8124"))
    mcp.run(transport="streamable-http", host=host, port=port)  # type: ignore[call-arg]
