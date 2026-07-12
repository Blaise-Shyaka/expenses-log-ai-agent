# Expenses MCP

FastMCP tool server that exposes 7 expense operations as MCP-compatible endpoints. The LangGraph agent connects to this server on startup to load its tools. Any other MCP client (Claude Desktop, Cursor, etc.) can connect to it directly.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- [Expenses API](../expenses-api/README.md) running at `http://localhost:8000`

## 1. Configure Environment

```bash
cp .env.example .env
```

The defaults in `.env.example` work as-is for local development. The only variable you might need to change is `EXPENSES_API_URL` if your API is running on a different address:

```
PORT=8124
EXPENSES_API_URL=http://localhost:8000/api/v1
```

## 2. Install Dependencies

```bash
uv sync
```

## 3. Start the Server

```bash
uv run python main.py
```

The MCP server is now running at `http://localhost:8124`.

- **MCP endpoint**: `http://localhost:8124/mcp`
- **Health check**: `http://localhost:8124/health`

## Exposed Tools

The server exposes 7 tools that the LLM uses to record and query expenses:

| Tool | Description |
|---|---|
| `get_all_expenses` | List all expenses (first 100) |
| `create_expense_category` | Create a new expense category |
| `get_all_categories` | List all categories (first 100) |
| `get_category_by_name` | Look up a category by name |
| `create_expense` | Record a new expense |
| `get_expenses_by_category` | Totals grouped by category |
| `get_expenses_since` | Total since a date or number of days (optional category filter) |

## Connecting from Claude Desktop

Add this to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "expenses": {
      "url": "http://localhost:8124/mcp"
    }
  }
}
```

The expenses tools will then be available in any Claude Desktop conversation.
