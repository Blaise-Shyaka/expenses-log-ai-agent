# AGENTS.md

## Project Overview

Three-package monorepo: AI expense tracking via chat. User pastes an SMS/email confirmation → LangGraph agent extracts and categorizes it → stored via FastAPI → shown in CopilotKit chat UI.

```
expenses-agent/   # LangGraph AI agent (Python, FastAPI wrapper, port 8123)
expenses-api/     # FastAPI REST API (Python, async SQLAlchemy, port 8000 → internal :52)
ui/               # Next.js 15 frontend (TypeScript, CopilotKit chat, port 3000)
```

---

## Running Locally

**Start backend (API + Agent + MySQL):**
```bash
docker compose up --build
```
Migration runs automatically via the `migration` service before the API starts.

**Start UI (separate terminal — run outside Docker for faster dev):**
```bash
cd ui && npm install && npm run dev
```

**Optional — Ollama (local LLM):**
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

---

## Environment Variables

Each package has its own `.env` (copy from `.env.example`). No shared root `.env`.

**`expenses-agent/.env`:**
- `GOOGLE_API_KEY` — Gemini API key (only needed if `USE_LOCAL_MODEL=false`)
- `EXPENSES_API_URL` — defaults to `http://0.0.0.0:8000/api/v1` for local dev; Docker Compose overrides to `http://expenses-api:52/api/v1` via environment block in `compose.yml`
- `USE_LOCAL_MODEL=true` — toggles Ollama vs Gemini
- `LANGSMITH_API_KEY` — optional tracing

**`expenses-api/.env`:**
- MySQL vars (`MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`)
- `DATABASE_URL` — async driver: `mysql+aiomysql://...`
- `ALEMBIC_URL` — sync driver: `mysql+pymysql://...` (different driver from app!)

**`ui/.env`:**
- `AGENT_URL` — defaults to `http://localhost:8123`
- `GOOGLE_API_KEY` — used by `ExperimentalOllamaAdapter` in the CopilotKit route (note: despite the name, the UI route uses Ollama adapter with model `llama:3.2`)

---

## Port Map

| Service | External | Internal |
|---|---|---|
| expenses-api | 8000 | 52 (non-standard — healthcheck uses `:52/docs`) |
| expenses-agent | 8123 | 8123 |
| MySQL | (Docker internal) | 3306 |
| ui | 3000 | 3000 |

**Quirk:** The API runs on internal port **52** (not 8000). Compose maps `8000:52`. Do not change this without updating the healthcheck in `compose.yml`.

---

## Package Managers & Tooling

- `expenses-agent` and `expenses-api`: **`uv`** (Python ≥ 3.13, lockfiles in `uv.lock`)
- `ui`: **npm** (Next.js 15 with Turbopack)
- No root-level Python venv — each package has its own `.venv/`

---

## Type Checking

Pyright in **strict mode** covers `expenses-agent/` and `expenses-api/`. Two files are excluded from strict checking (langgraph has no stubs):
- `expenses-agent/src/tools.py`
- `expenses-agent/src/llm.py`

The `# type: ignore` comments in `main.py` are intentional due to missing langgraph stubs — do not remove them.

---

## Database & Migrations

- MySQL with **UUID stored as `BINARY(16)`** — not as VARCHAR. IDs are stored as `.bytes`, not as UUID strings.
- ORM: SQLAlchemy async (`aiomysql` driver for app, `pymysql` for Alembic)
- Run migrations: `alembic upgrade head` (from `expenses-api/`)
- Docker Compose runs migrations via the `migration` service automatically.

**Critical:** A seed migration (`b1234567890a`) inserts a hardcoded test user:
- UUID: `00000000-0000-0000-0000-000000000001`
- All expenses and categories are currently tied to this user (`TEST_USER_ID_BYTES` from `core/constants.py`)
- **Auth is not implemented.** Every endpoint uses this hardcoded user. Do not build auth assumptions into data layer without removing `TEST_USER_ID_BYTES` references first.

---

## Agent Architecture

**Graph** (`expenses-agent/main.py`):
```
START → gemini_node → [tools_condition] → tools → gemini_node → END
```
- `gemini_node`: prepends system prompt to state messages, calls bound LLM
- `tools`: `ToolNode` wrapping 7 tool functions in `src/tools.py`
- `MemorySaver` checkpointer for in-memory conversation state
- Agent name: `"Reddington"` (used by CopilotKit to route `agent="chat"`)

**LLM selection** (`src/llm.py`):
- `USE_LOCAL_MODEL=true` → `ChatOllama` (llama3.2, localhost:11434)
- `USE_LOCAL_MODEL=false` → `ChatGoogleGenerativeAI` (gemini-2.0-flash-lite) with `InMemoryRateLimiter` at 0.2 req/s

**Tools** are plain Python functions with docstrings — LangChain uses the docstrings as tool descriptions for the LLM. Keep docstrings accurate and detailed.

---

## UI / CopilotKit Wiring

- `ui/app/api/copilotkit/route.ts` — Next.js route handler, `POST` only
- Uses `ExperimentalOllamaAdapter` with `model: 'llama:3.2'` regardless of the `GOOGLE_API_KEY` env var being present
- Connects to agent via `LangGraphHttpAgent` at `AGENT_URL`
- Frontend: single page, `CopilotKit` wraps `CopilotChat` with `agent="chat"` targeting the `chat` graph

---

## Known Duplication / Tech Debt

- `expenses-agent/src/types.py` is a copy of `expenses-api/schemas/schema.py` — tracked in [issue #16](https://github.com/Blaise-Shyaka/momo-expenses-langraph-ai-agent/issues/16). Do not add new types to only one side without updating the other.
- `TEST_USER_ID_BYTES` is used everywhere auth should be — flagged with `TODO` comments in endpoints and constants.
- The agent healthcheck URL in `compose.yml` is a LangSmith Studio URL — noted with a `# Find a better way` comment.
- Logging is configured via `logging.basicConfig` directly in `tools.py` — noted with a `# Worth moving` comment.

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

API docs auto-generated at `http://localhost:8000/docs` (maps to internal `:52/docs`).

---

## No Tests

There are no test files in this repo. Do not assume a test suite exists. If adding tests, use pytest (consistent with the Python toolchain).
