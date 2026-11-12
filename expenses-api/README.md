# Expenses API

FastAPI app that serves the REST API for storing and querying expenses (`/api/v1`) and the chat agent (`/agent`). It uses Async SQLAlchemy + MySQL, and migrations via Alembic. The agent is a LangGraph graph in the `agent` package; it still loads its tools from [expenses-mcp](../expenses-mcp/README.md).

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Docker — for running MySQL locally
- For `/agent`: [expenses-auth](../expenses-auth/README.md) and [expenses-mcp](../expenses-mcp/README.md) running, and a DeepSeek API key or a local Ollama

## 1. Start MySQL

```bash
docker run --rm -d \
  --name expenses-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=expenses_dev \
  -e MYSQL_USER=dev_user \
  -e MYSQL_PASSWORD=secret \
  mysql:8
```

> **Note:** `--rm` removes the container when stopped. All data is lost on restart. Drop `--rm` if you want persistence between sessions.

## 2. Configure Environment

```bash
cp .env.example .env
```

Then edit `.env`. Replace the placeholder values with what you used above:

```
DATABASE_URL="mysql+aiomysql://dev_user:secret@localhost:3306/expenses_dev"
ALEMBIC_URL="mysql+pymysql://dev_user:secret@localhost:3306/expenses_dev"
```

> Both URLs point to the same database but use different drivers. `DATABASE_URL` uses `aiomysql` (async, for the app). `ALEMBIC_URL` uses `pymysql` (sync, for migrations). Both are required.

Set the JWT auth variables to point to your auth service:

```
AUTH_JWKS_URI="https://auth.example.com/.well-known/jwks.json"
AUTH_ISSUER="https://auth.example.com"
AUTH_AUDIENCE="expenses-api"
AUTH_REQUIRED=true
```

`AUTH_JWKS_URI`, `AUTH_ISSUER` and `AUTH_REQUIRED` apply to both `/api/v1` and `/agent`. `AUTH_AUDIENCE` applies to `/api/v1` only, and stays `expenses-api` while `expenses-mcp` calls the API with its service token. `/agent` checks user tokens for audience `expenses-agent`, the audience `expenses-auth` gives them.

Set `AUTH_REQUIRED=false` to bypass authentication in local development: `/api/v1` requests pass through unauthenticated and `/agent` runs every request as the dev user `00000000-0000-0000-0000-000000000001`. **Never use this in production.** Set `DEBUG=true` to re-enable `/docs`, `/redoc`, and `/openapi.json`.

### Agent

The agent at `/agent` is off unless a model is configured. You need **either** DeepSeek **or** Ollama:

```
DEEPSEEK_API_KEY=sk-...          # from platform.deepseek.com
OLLAMA_URL=http://localhost:11434  # a value here takes precedence; blank means DeepSeek
```

To run Ollama with llama3.2:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

The agent loads its tools from the MCP server, using a service token from `expenses-auth`:

```
MCP_URL=http://localhost:8124
AUTH_TOKEN_URL=http://localhost:8001/oauth/token
AGENT_CLIENT_ID=svc-agent
AGENT_CLIENT_SECRET=<the SVC_AGENT_SECRET given to expenses-auth>
```

The agent starts in the background, so the REST API serves straight away. Until it has loaded its tools, `/agent` answers 503 and `/health` shows `"agent": {"name": null}`; if startup fails it logs a warning and retries every 30 seconds.

Optional:

- `LLM_REQUESTS_PER_SECOND` caps model calls per second for the whole process, shared by every user. Unset means no limit. A value that is not a positive number stops the agent (not the API) from starting.
- `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` send traces to LangSmith; read by the LangSmith SDK.

## 3. Install Dependencies

```bash
uv sync
```

## 4. Run Migrations

Wait ~10 seconds for MySQL to be ready, then:

```bash
uv run alembic upgrade head
```

This creates the tables. A seed migration inserts a legacy test user row (`00000000-0000-0000-0000-000000000001`) that is preserved but no longer used by any endpoint.

## 5. Start the Server

```bash
uv run python main.py
```

For development with auto-reload:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The app is now running at `http://localhost:8000`: the REST API under `/api/v1`, the agent at `/agent` and a health check at `/health`. Point the UI's `AGENT_URL` at `http://localhost:8000/agent`.

### LangGraph Studio

To inspect the agent graph, step through tool calls and replay conversations:

```bash
uv run langgraph dev
```

`langgraph.json` loads the graph from `agent/graph.py:make_graph` and reads `.env`. It needs the MCP server and `expenses-auth`, like `/agent`. Safari blocks localhost connections; use `uv run langgraph dev --tunnel` there.

## Exploring the API

Interactive docs are disabled by default. Set `DEBUG=true` in `.env` and restart to enable:

| | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Raw OpenAPI JSON | http://localhost:8000/openapi.json |

### Import into Postman

1. Open Postman, then **Import**
2. Select **Link**, paste `http://localhost:8000/openapi.json`
3. All routes are imported with schemas and example bodies — no manual setup needed.

## API Routes

```
POST   /api/v1/expenses/                    Create expense (auto-creates category if missing)
GET    /api/v1/expenses/                    List expenses (skip/limit/category_name)
GET    /api/v1/expenses/{id}                Get single expense
GET    /api/v1/expenses/totals/by-category  Grouped totals by category
GET    /api/v1/expenses/totals/since        Total since date/days (optional category filter)

POST   /api/v1/categories/                  Create category
GET    /api/v1/categories/                  List categories
GET    /api/v1/categories/{id}              Get by UUID
GET    /api/v1/categories/name/{name}       Get by name (case-insensitive)

POST   /agent                               Chat with the agent (AG-UI event stream)
GET    /health                              Health check, with the agent's name once it has loaded
```
