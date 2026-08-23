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

Fill in the values for your environment. See the table below for all variables.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8124` | Port this MCP server listens on |
| `EXPENSES_API_URL` | `http://localhost:8000/api/v1` | URL of the expenses REST API |
| `AUTH_REQUIRED` | `true` | Set to `false` to disable inbound auth (dev only — logs a loud warning) |
| `AUTH_URL` | — | Auth service base URL (declared as OAuth authorization server in resource metadata) |
| `AUTH_JWKS_URI` | — | JWKS endpoint for RS256 JWT verification |
| `AUTH_ISSUER` | — | Expected `iss` claim in inbound JWTs |
| `MCP_BASE_URL` | — | Public base URL of this server (used in protected-resource metadata) |
| `MCP_CLIENT_ID` | — | `client_credentials` client ID for calling `expenses-api` |
| `MCP_CLIENT_SECRET` | — | `client_credentials` client secret |
| `AUTH_TOKEN_URL` | — | Token endpoint used to obtain outbound service tokens |

### Authentication

All `/mcp` requests require a valid RS256 JWT with `aud=expenses-mcp`, verified against `AUTH_JWKS_URI`. The `GET /health` endpoint is unauthenticated.

**Acting-user resolution** (per tool call):
- Token has `act-on-behalf` scope **and** `X-Acting-User` header present → acting user = header value
- `X-Acting-User` present without `act-on-behalf` → request rejected (ToolError)
- No `X-Acting-User` header → acting user = token `sub` (falls back to `client_id`)

**Outbound calls** to `expenses-api` attach a `Bearer` service token (`aud=expenses-api`) obtained via `client_credentials` (cached, renewed ~60s before expiry) plus `X-Acting-User`.

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
