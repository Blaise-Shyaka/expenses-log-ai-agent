import os

from dotenv import load_dotenv

load_dotenv()

from src.mcp_server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8124)))  # type: ignore[call-arg]
