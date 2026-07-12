# AGENTS.md

## Project Overview

Four-package monorepo: AI expense tracking via chat. User pastes an SMS/email confirmation → LangGraph agent extracts and categorizes it → MCP server calls the REST API → stored in MySQL → shown in CopilotKit chat UI.

```
expenses-agent/   # LangGraph AI agent (Python, FastAPI wrapper, port 8123)
expenses-mcp/     # FastMCP tool server (Python, port 8124)
expenses-api/     # FastAPI REST API (Python, async SQLAlchemy, port 8000)
ui/               # Next.js 15 frontend (TypeScript, CopilotKit chat, port 3000)
```

---

## Running Locally

Each service runs independently. Start them in order:

1. **`expenses-api`** — see [expenses-api/README.md](expenses-api/README.md). Starts MySQL and the REST API.
2. **`expenses-mcp`** — see [expenses-mcp/README.md](expenses-mcp/README.md). Starts the MCP tool server (depends on the API).
3. **`expenses-agent`** — see [expenses-agent/README.md](expenses-agent/README.md). Starts the LangGraph agent (depends on the MCP server).
4. **`ui`** — see [ui/README.md](ui/README.md). Starts the chat interface.

**Optional — Ollama (local LLM):**
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

---

## Environment Variables

Each package has its own `.env` (copy from `.env.example`). No shared root `.env`.

**`expenses-agent/.env`:**
- `DEEPSEEK_API_KEY` — DeepSeek API key (only needed if `OLLAMA_URL` is not set)
- `OLLAMA_URL` — Ollama base URL (e.g. `http://localhost:11434`); takes precedence over DeepSeek when set
- `MCP_URL` — URL of the MCP tool server; defaults to `http://localhost:8124`
- `LANGSMITH_API_KEY` — optional tracing
- `LANGSMITH_TRACING` — set to `true` to enable passive tracing to LangSmith
- `LANGSMITH_PROJECT` — organizes traces by project in LangSmith
- `PORT` — port this agent listens on; defaults to `8123`

**`expenses-mcp/.env`:**
- `EXPENSES_API_URL` — URL of the REST API; defaults to `http://localhost:8000/api/v1`
- `PORT` — port this MCP server listens on; defaults to `8124`

**`expenses-api/.env`:**
- MySQL vars (`MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`)
- `DATABASE_URL` — async driver: `mysql+aiomysql://...`
- `ALEMBIC_URL` — sync driver: `mysql+pymysql://...` (different driver from app!)

**`ui/.env`:**
- `AGENT_URL` — defaults to `http://localhost:8123`

---

## Port Map

| Service | Port |
|---|---|
| expenses-api | 8000 |
| expenses-mcp | 8124 |
| expenses-agent | 8123 |
| MySQL | 3306 |
| ui | 3000 |

---

## Package Managers & Tooling

- `expenses-agent`, `expenses-mcp`, and `expenses-api`: **`uv`** (Python ≥ 3.13, lockfiles in `uv.lock`)
- `ui`: **npm** (Next.js 15 with Turbopack)
- No root-level Python venv — each package has its own `.venv/`

---

## Type Checking

Pyright in **strict mode** covers `expenses-agent/`, `expenses-mcp/`, and `expenses-api/`. Each package has its own `pyrightconfig.json`.

The `# type: ignore` and `# pyright: ignore` comments throughout the agent code are intentional — langgraph and ag-ui-langgraph have no type stubs. Do not remove them.

---

## Database & Migrations

- MySQL with **UUID stored as `BINARY(16)`** — not as VARCHAR. IDs are stored as `.bytes`, not as UUID strings.
- ORM: SQLAlchemy async (`aiomysql` driver for app, `pymysql` for Alembic)
- Run migrations: `alembic upgrade head` (from `expenses-api/`)

**Critical:** A seed migration (`b1234567890a`) inserts a hardcoded test user:
- UUID: `00000000-0000-0000-0000-000000000001`
- All expenses and categories are currently tied to this user (`TEST_USER_ID_BYTES` from `core/constants.py`)
- **Auth is not implemented.** Every endpoint uses this hardcoded user. Do not build auth assumptions into data layer without removing `TEST_USER_ID_BYTES` references first.

---

## Agent Architecture

**Graph** (`expenses-agent/src/graph.py`):
```
START → llm_node → [tools_condition] → tools → llm_node → END
```
- `llm_node`: prepends system prompt to state messages, calls bound LLM
- `tools`: `ToolNode` wrapping 7 MCP tools loaded from the MCP server at startup
- `MemorySaver` checkpointer for in-memory conversation state

**Graph factory** (`src/graph.py:make_graph`):
- `@asynccontextmanager` — used by both `langgraph dev` (via `langgraph.json`) and standalone FastAPI (via `main.py` lifespan)
- On startup: polls `MCP_URL/health` until the MCP server is ready, then loads tools via `MultiServerMCPClient` (`langchain-mcp-adapters`)
- `langgraph.json` points to `./main.py:make_graph` — `main.py` re-exports the factory so `langgraph dev` loads it from the package root with correct import context

**FastAPI wiring** (`main.py`):
- Uses `ag-ui-langgraph`: `add_langgraph_fastapi_endpoint` mounts the graph as an AG-UI endpoint at `/`
- `LangGraphAGUIAgent(name="Reddington")` — the name `"Reddington"` is what `langgraph.json` exposes as the `chat` graph key, which the UI targets with `agent="chat"`
- The agent serves the AG-UI streaming protocol (not raw LangGraph HTTP); this is what CopilotKit's `LangGraphHttpAgent` connects to

**LLM selection** (`src/llm.py`):
- `OLLAMA_URL` set → `ChatOllama` (llama3.2, at the configured URL)
- `OLLAMA_URL` not set → `ChatDeepSeek` (deepseek-chat) with `InMemoryRateLimiter` at 0.2 req/s

---

## MCP Server Architecture

**Server** (`expenses-mcp/src/mcp_server.py`):
- Built with [FastMCP](https://github.com/jlowin/fastmcp), runs on port 8124
- Transport: `streamable-http` — MCP endpoint at `/mcp`, health check at `/health`
- Exposes 7 tools decorated with `@mcp.tool`; docstrings are used by the LLM as tool descriptions — keep them accurate

**Tools** (`expenses-mcp/src/tools.py`):
- Each tool makes synchronous HTTP requests to `expenses-api` via `requests`
- Retry logic: 3 attempts with exponential backoff on connection errors

**7 exposed tools:**
1. `get_all_expenses` — list all expenses (first 100)
2. `create_expense_category` — create a new category
3. `get_all_categories` — list all categories
4. `get_category_by_name` — look up a category by name
5. `create_expense` — record a new expense
6. `get_expenses_by_category` — totals grouped by category
7. `get_expenses_since` — total since a date or number of days (optional category filter)

---

## UI / CopilotKit Wiring

- `ui/app/api/copilotkit/route.ts` — Next.js route handler, `POST` only
- Connects to agent via `LangGraphHttpAgent` at `AGENT_URL`
- Frontend: single page, `CopilotKit` wraps `CopilotChat` with `agent="chat"` targeting the `chat` graph

---

## Known Duplication / Tech Debt

- `expenses-mcp/src/types.py` is a copy of `expenses-api/schemas/schema.py` — tracked in [issue #16](https://github.com/Blaise-Shyaka/momo-expenses-langraph-ai-agent/issues/16). Do not add new types to only one side without updating the other.
- `TEST_USER_ID_BYTES` is used everywhere auth should be — flagged with `TODO` comments in endpoints and constants.
- Logging is configured via `logging.basicConfig` directly in `expenses-mcp/src/tools.py` — noted with a `# Worth moving` comment.

---

## API Routes

```
POST   /api/v1/expenses/                   create expense (auto-creates category if missing)
GET    /api/v1/expenses/                   list expenses (skip/limit/category_name)
GET    /api/v1/expenses/{id}               get single expense
GET    /api/v1/expenses/totals/by-category grouped totals
GET    /api/v1/expenses/totals/since       total since date/days (optional category filter)

POST   /api/v1/categories/                 create category
GET    /api/v1/categories/                 list categories
GET    /api/v1/categories/{id}             get by UUID
GET    /api/v1/categories/name/{name}      get by name (case-insensitive)
```

API docs auto-generated at `http://localhost:8000/docs`.

---

## No Tests

There are no test files in this repo. Do not assume a test suite exists. If adding tests, use pytest (consistent with the Python toolchain).
