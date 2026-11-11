# AGENTS.md

## Project Overview

Five-service monorepo: AI expense tracking via chat. A signed-in user pastes an SMS or email payment confirmation, a LangGraph agent extracts and categorizes it, and each tool call goes from the agent to the MCP server to the REST API to MySQL. The result shows in a CopilotKit chat UI.

This file describes the code as it is. The agreed target (one Python app on one Postgres, sign-in through WorkOS AuthKit) and the order of work are in [docs/architecture.md](docs/architecture.md).

```
expenses-auth/    # Go auth service: login, refresh and service tokens, JWKS (port 8001, Postgres)
expenses-api/     # FastAPI REST API, async SQLAlchemy (port 8000, MySQL)
expenses-mcp/     # FastMCP tool server over streamable HTTP (port 8124)
expenses-agent/   # LangGraph agent behind FastAPI, speaks AG-UI (port 8123)
ui/               # Next.js 16 chat UI with CopilotKit and next-auth (port 3000)
```

---

## Running Locally

Each service runs on its own; there is no compose file. Start them in this order:

1. **`expenses-auth`**: see [expenses-auth/README.md](expenses-auth/README.md). Set `SVC_AGENT_SECRET` and `SVC_MCP_SECRET` so the two machine clients are seeded, and `SEED_DEV_USER=true` for a dev login (`dev@localhost` / `dev`). Without `DATABASE_URL` it uses an in-memory store that is lost on restart.
2. **`expenses-api`**: see [expenses-api/README.md](expenses-api/README.md). Starts MySQL, runs migrations and serves the REST API.
3. **`expenses-mcp`**: see [expenses-mcp/README.md](expenses-mcp/README.md). Starts the MCP tool server.
4. **`expenses-agent`**: see [expenses-agent/README.md](expenses-agent/README.md). On startup it polls `MCP_URL/health` (10 tries with backoff), fetches a service token from `expenses-auth`, then loads its tools from the MCP server. It fails to start if either is unreachable.
5. **`ui`**: see [ui/README.md](ui/README.md). Starts the chat interface.

`expenses-auth` is needed even with `AUTH_REQUIRED=false`; see [Auth-off mode](#auth-off-mode).

**Optional — Ollama (local LLM):**
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

---

## Port Map

| Service | Port | Variable |
|---|---|---|
| expenses-auth | 8001 | `PORT` |
| Postgres (auth) | 5432 | in `DATABASE_URL` |
| expenses-api | 8000 | `PORT` |
| MySQL | 3306 | in `DATABASE_URL` |
| expenses-mcp | 8124 | `PORT` |
| expenses-agent | 8123 | `PORT` |
| ui | 3000 | `PORT` (Dockerfile) |

---

## Environment Variables

Each package has its own `.env` (copy from `.env.example`). There is no shared root `.env`. The Python services load `.env` themselves (`python-dotenv` in the agent and MCP, `pydantic-settings` in the API); Next.js loads it for the UI; `expenses-auth` reads only the process environment.

**`expenses-auth`** (`main.go`):
- `PORT` — defaults to `8001`
- `DATABASE_URL` — Postgres URL; unset means an in-memory store
- `SIGNING_KEY_PEM` — RSA private key as PEM; takes precedence over `SIGNING_KEY_PATH`
- `SIGNING_KEY_PATH` — key file, defaults to `signing.key`; generated if missing
- `ISSUER_URL` — the `iss` claim; defaults to `http://localhost:8001`
- `SVC_AGENT_SECRET`, `SVC_MCP_SECRET` — secrets for the `svc-agent` and `svc-mcp` clients; both must be set or neither client is seeded
- `SEED_DEV_USER` — `true` seeds `dev@localhost` / `dev` with id `00000000-0000-0000-0000-000000000001`

**`expenses-api`** (`config/db_config.py`, `main.py`):
- `DATABASE_URL` — async driver: `mysql+aiomysql://...`
- `ALEMBIC_URL` — sync driver: `mysql+pymysql://...` (different driver from the app)
- `AUTH_JWKS_URI`, `AUTH_ISSUER` — where to verify tokens
- `AUTH_AUDIENCE` — expected `aud`; defaults to `expenses-api`
- `AUTH_REQUIRED` — defaults to `true`
- `DEBUG` — `true` serves `/docs`, `/redoc` and `/openapi.json`; off by default
- `PORT` — defaults to `8000`; read from the process environment, not from `.env`
- `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` — for the MySQL container only; the app does not read them

**`expenses-mcp`** (`src/mcp_server.py`, `src/token_client.py`, `src/tools.py`):
- `PORT` — defaults to `8124`
- `EXPENSES_API_URL` — defaults to `http://localhost:8000/api/v1`
- `AUTH_REQUIRED` — defaults to `true`
- `AUTH_JWKS_URI`, `AUTH_ISSUER` — where to verify incoming tokens
- `AUTH_URL` — advertised to MCP clients as the authorization server; defaults to `http://localhost:8001`
- `MCP_BASE_URL` — this server's public URL
- `AUTH_TOKEN_URL`, `MCP_CLIENT_ID`, `MCP_CLIENT_SECRET` — client credentials for the outbound token to the API; tool calls fail if any is missing

**`expenses-agent`** (`src/llm.py`, `src/auth.py`, `src/token_client.py`, `src/mcp_client.py`, `main.py`):
- `OLLAMA_URL` — if present, the agent uses Ollama, even when the value is empty
- `DEEPSEEK_API_KEY` — used when `OLLAMA_URL` is absent
- `MCP_URL` — defaults to `http://localhost:8124`
- `PORT` — defaults to `8123`
- `AUTH_REQUIRED` — defaults to `true`
- `AUTH_JWKS_URI`, `AUTH_ISSUER` — where to verify user tokens
- `AUTH_TOKEN_URL`, `AGENT_CLIENT_ID`, `AGENT_CLIENT_SECRET` — client credentials for the outbound token to the MCP server
- `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` — optional; read by the LangSmith SDK, not by our code

**`ui`** (`app/api/copilotkit/route.ts`, `lib/expenses-auth-client.ts`, `auth.ts`, `proxy.ts`):
- `AGENT_URL` — defaults to `http://localhost:8123`
- `AUTH_SERVICE_URL` — defaults to `http://localhost:8001`
- `AUTH_SECRET` — next-auth secret for the session cookie
- `AUTH_TRUST_HOST` — `true` lets next-auth build redirects from the reverse proxy's forwarded headers

---

## Auth Flow

`expenses-auth` signs every token with RS256 and publishes its keys at `/.well-known/jwks.json`. Its routes are `POST /register`, `POST /login`, `POST /oauth/token` (`client_credentials` and `refresh_token` grants), the JWKS route and `GET /health`.

| Token | Obtained by | `aud` | `scope` | Lifetime |
|---|---|---|---|---|
| User access token | ui, from `/login` or a refresh | `expenses-agent` | `chat` | 15 min |
| Refresh token | ui, from `/login`; rotated on each refresh | opaque, stored hashed | — | 30 days |
| `svc-agent` service token | agent, `client_credentials` | `expenses-mcp` | `mcp:call act-on-behalf` | 15 min |
| `svc-mcp` service token | MCP, `client_credentials` | `expenses-api` | `expenses:read expenses:write act-on-behalf` | 15 min |

A chat message travels like this:

1. `ui/proxy.ts` redirects to `/login` unless there is a next-auth session with no refresh error.
2. The next-auth credentials provider (`ui/auth.ts`) posts to `AUTH_SERVICE_URL/login` and keeps both tokens in next-auth's JWT session cookie. It refreshes the access token 2 minutes before it expires. Registration posts to `/register` (`ui/app/actions/auth-actions.ts`).
3. The browser sends `Authorization: Bearer <access token>` with each CopilotKit request (`ui/app/page.tsx`). `/api/copilotkit` returns 401 without it, and CopilotKit forwards the header to the agent.
4. The agent (`main.py`, `src/auth.py`) verifies the token against the JWKS with audience `expenses-agent`, takes `sub` as the acting user and prefixes the thread id with it.
5. For each tool call, `src/mcp_interceptor.py` attaches the agent's service token and `X-Acting-User: <sub>`.
6. The MCP server verifies the token with audience `expenses-mcp`. `src/auth.py:resolve_acting_user` accepts `X-Acting-User` only from a token with the `act-on-behalf` scope, and otherwise uses the token's `sub`. It then calls the API with its own service token and the same `X-Acting-User`.
7. The API (`core/security.py`) verifies the token with audience `AUTH_AUDIENCE` and applies the same `act-on-behalf` rule. Endpoints require `expenses:read` or `expenses:write`, and repositories are built with the acting user's id. The user's row in the API database is created on their first write (`UsersRepository.ensure`).

### Auth-off mode

The agent, MCP server and API each accept `AUTH_REQUIRED=false`, which skips verification of incoming tokens in that service only. Never use it in production.

- **Agent:** every request runs as the dev user `00000000-0000-0000-0000-000000000001`.
- **MCP:** tool calls fail, because `resolve_acting_user` needs a verified token.
- **API:** repositories are built with `user_id=None`, so reads are not scoped to any user.
- The agent and MCP still fetch service tokens from `expenses-auth` for their outbound calls, so it must be running.
- The UI has no bypass.

---

## Agent Architecture

**FastAPI wiring** (`expenses-agent/main.py`):
- `POST /` verifies the user token, sets the acting user and the browser's timezone (`forwarded_props.timezone`) in context variables (`src/context.py`), and streams `LangGraphAGUIAgent(name="Reddington").run(...)` as AG-UI events. `GET /health` returns the agent's name once the graph is loaded.
- `chat` is the agent name the UI registers in `ui/app/api/copilotkit/route.ts`, where `LangGraphHttpAgent` points at `AGENT_URL`. `langgraph.json` also names the graph `chat`, for `langgraph dev`.

**Graph** (`expenses-agent/src/graph.py`):
```
START → llm_node → [tools_condition] → tools → llm_node → END
```
- `llm_node` prepends the system prompt, with today's date in the request's timezone (UTC by default), and calls the bound LLM.
- `tools` is a `ToolNode` wrapping the 7 MCP tools loaded once at startup with `MultiServerMCPClient`.
- A `MemorySaver` checkpointer keeps conversation state in process memory, so it is lost on every restart.
- `make_graph` is an `@asynccontextmanager` used by both the FastAPI lifespan and `langgraph dev` (`langgraph.json` points at `./main.py:make_graph`, which re-exports it).

**LLM selection** (`src/llm.py`):
- `OLLAMA_URL` present → `ChatOllama` (llama3.2)
- otherwise → `ChatDeepSeek` (deepseek-chat) with one `InMemoryRateLimiter` at 0.2 requests per second for the whole process

---

## MCP Server Architecture

**Server** (`expenses-mcp/src/mcp_server.py`):
- Built with [FastMCP](https://github.com/jlowin/fastmcp) as `expenses-tools`; transport is `streamable-http`, with the MCP endpoint at `/mcp` and a health check at `/health`.
- With auth on, a `JWTVerifier` (audience `expenses-mcp`) sits behind a `RemoteAuthProvider` that names `AUTH_URL` as the authorization server.
- Each tool is a thin `@mcp.tool` wrapper: it resolves the acting user, builds the outbound headers and calls the matching function in `tools.py`. Docstrings are the tool descriptions the LLM sees; keep them accurate.

**Tools** (`expenses-mcp/src/tools.py`):
- Each call is a synchronous `requests` call to `expenses-api`, made from the async tool function, so every tool call is a network round trip from agent to MCP to API.
- A shared `requests.Session` retries up to 3 times with backoff, including on 500, 502, 503 and 504. No request timeout is set.

**7 exposed tools:**
1. `get_all_expenses` — list expenses
2. `create_expense_category` — create a new category
3. `get_all_categories` — list categories
4. `get_category_by_name` — look up a category by name
5. `create_expense` — record a new expense
6. `get_expenses_by_category` — totals grouped by category
7. `get_expenses_since` — total since a date or number of days (optional category filter)

---

## API Architecture

`expenses-api` is layered: endpoints (`api/v1/endpoints/`) → services (`services/`) → repositories (`db/repositories/`).
- `enforce_auth` (`core/security.py`) is an app-wide dependency that verifies the bearer token on every route except `/health`.
- Endpoints own HTTP and auth concerns: `check_scope`, `get_principal`. Wiring lives in `api/deps.py`.
- Services hold business rules and raise domain exceptions (`exceptions/custom_exceptions.py`), which `main.py` maps to HTTP status codes. Services never raise `HTTPException`.
- `CategoryRepository` and `ExpensesRepository` are built with the acting user's id and scope every query to it (`None` only when auth is disabled). New queries must go through `_scoped()` or filter on `self.user_id`.
- Repositories only `flush`; the service commits once through `UnitOfWork`, so a request's writes are atomic.

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

GET    /health                             no auth
```

`POST` routes need the `expenses:write` scope and `GET` routes need `expenses:read`. With `DEBUG=true`, the generated docs are at `http://localhost:8000/docs`.

---

## Database & Migrations

**`expenses-api` (MySQL):**
- UUIDs are stored as `BINARY(16)`, not as VARCHAR. IDs are stored as `.bytes`, not as UUID strings.
- ORM: SQLAlchemy async (`aiomysql` for the app, `pymysql` for Alembic).
- Run migrations from `expenses-api/`: `uv run alembic upgrade head`.
- The seed migration `b1234567890a` inserts a user with id `00000000-0000-0000-0000-000000000001`, the same id as the `expenses-auth` dev user and the agent's auth-off user.
- Amounts are `Float` with no currency, and dates are naive `DateTime`.

**`expenses-auth` (Postgres):** the schema is in `internal/store/migrations/`, embedded in the binary and applied on startup.

---

## Package Managers & Tooling

- `expenses-agent`, `expenses-mcp` and `expenses-api`: **`uv`**, Python ≥ 3.13, each with its own `uv.lock` and `.venv/`. There is no root-level Python venv.
- `expenses-auth`: Go 1.25 (`go.mod`).
- `ui`: **pnpm** (`ui/pnpm-lock.yaml`, `ui/pnpm-workspace.yaml`); CI uses Node 24. The root `package.json` and `pnpm-lock.yaml` hold no dependencies.

## Type Checking and Lint

Pyright in **strict mode** covers `expenses-agent/`, `expenses-mcp/` and `expenses-api/`, each with its own `pyrightconfig.json`. The checks CI runs per package are listed in [CLAUDE.md](CLAUDE.md).

The `# type: ignore` and `# pyright: ignore` comments throughout the agent code are intentional: langgraph and ag-ui-langgraph have no type stubs. Do not remove them.

## CI and Deploys

- `.github/workflows/lint.yml` runs on pull requests to `main` and on pushes to `main`, with one job per service.
- `build-dev.yml` runs on pushes to `main`. It builds images for the services that changed, pushes them to GHCR as `:dev` and `:sha-<commit>`, and redeploys them on Coolify.
- `promote-prod.yml` runs when a release is published and promotes each service's `:dev` image to production.

---

## Known Duplication / Tech Debt

- `expenses-mcp/src/types.py` is a copy of `expenses-api/schemas/schema.py`, tracked in #16. Do not add a type to one side without updating the other.
- `expenses-mcp/src/tools.py` configures logging with `logging.basicConfig` directly, noted with a `# Worth moving` comment.

---

## Tests

- `expenses-api`: `uv run pytest` from `expenses-api/`, run in CI. The tests use in-memory SQLite through `aiosqlite`, so no MySQL is needed.
- `expenses-auth`: `go test ./...` from `expenses-auth/`. The tests use the in-memory store, so no Postgres is needed.
- `expenses-agent`, `expenses-mcp` and `ui` have no tests yet; if adding some to a Python package, use pytest.
