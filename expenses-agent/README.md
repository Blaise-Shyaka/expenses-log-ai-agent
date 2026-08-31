# Expenses Agent

LangGraph AI agent that understands, categorizes, and records expenses. Talks to the user via a CopilotKit chat interface and calls tools exposed by the MCP server. Runs as a FastAPI server on port 8123.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/), a Python package manager
- [Expenses MCP](../expenses-mcp/README.md) running at `http://localhost:8124`

## 1. Configure Environment

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | Only if `OLLAMA_URL` is unset | _(none)_ | DeepSeek API key. Ignored entirely when `OLLAMA_URL` is set. |
| `OLLAMA_URL` | Only if `DEEPSEEK_API_KEY` is unset | _(none)_ | Local Ollama base URL. Takes precedence over DeepSeek when set. |
| `LANGSMITH_API_KEY` | No | _(none)_ | Optional — enables tracing to LangSmith. |
| `LANGSMITH_TRACING` | No | _(none)_ | Optional — set to `true` to enable passive tracing. |
| `LANGSMITH_PROJECT` | No | _(none)_ | Optional — organizes traces by project name. |
| `PORT` | No | `8123` | Port the agent listens on (standalone server mode only). |
| `MCP_URL` | No | `http://localhost:8124` | URL of the MCP tool server. |
| `AUTH_JWKS_URI` | Only if `AUTH_REQUIRED=true` | _(none)_ | JWKS endpoint used to verify incoming user JWTs. |
| `AUTH_ISSUER` | Only if `AUTH_REQUIRED=true` | _(none)_ | Expected `iss` claim in incoming user JWTs. |
| `AUTH_TOKEN_URL` | **Yes** | _(none)_ | Token endpoint used to fetch the agent's own service token. Used on every tool call regardless of `AUTH_REQUIRED` — missing it raises an error the first time a tool runs. |
| `AGENT_CLIENT_ID` | **Yes** | _(none)_ | `client_credentials` client ID. Same failure mode as `AUTH_TOKEN_URL`. |
| `AGENT_CLIENT_SECRET` | **Yes** | _(none)_ | `client_credentials` client secret. Same failure mode as `AUTH_TOKEN_URL`. |
| `AUTH_REQUIRED` | No | `true` | Set to `false` to skip verifying incoming user JWTs and use a hardcoded dev user id instead. Does **not** affect the outbound service-token vars above, which are always required. |

Open `.env` and fill in your LLM credentials. You need **either** DeepSeek **or** Ollama. Not both. We chose deepseek, since it's good value for money.

### Option A: DeepSeek (cloud)

Get an API key at [platform.deepseek.com](https://platform.deepseek.com):

```
DEEPSEEK_API_KEY=sk-...
```

### Option B: Ollama (local)

Run Ollama with llama3.2, or any other model you're comfortable with, then set its URL:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

```
OLLAMA_URL=http://localhost:11434
```

> If `OLLAMA_URL` is set, it takes precedence and DeepSeek is ignored.

### MCP Server URL

The default value in `.env.example` works as-is for local development:

```
MCP_URL=http://localhost:8124
```

> The agent connects to this URL on startup to load its tools. It retries with exponential backoff, so it tolerates the MCP server not being immediately ready.

### Auth Service

The agent validates incoming user JWTs and obtains its own service token for downstream MCP calls. Set these variables to point at your auth service:

```
AUTH_JWKS_URI=http://localhost:8001/.well-known/jwks.json
AUTH_ISSUER=http://localhost:8001
AUTH_TOKEN_URL=http://localhost:8001/oauth/token
AGENT_CLIENT_ID=svc-agent
AGENT_CLIENT_SECRET=<your-client-secret>
AUTH_REQUIRED=true
```

Set `AUTH_REQUIRED=false` during local development without an auth service — the agent will skip JWT verification and use the hardcoded dev user id. **Never use this in production.**

## 2. Install Dependencies

```bash
uv sync
```

## 3. Start the Agent

### Option A: With LangGraph Studio (recommended for development)

```bash
uv run langgraph dev
```

This starts the agent and prints three URLs:

```
🚀 API:       http://127.0.0.1:2024
🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
📚 API Docs:  http://127.0.0.1:2024/docs
```

Open the Studio URL to visually inspect the agent graph, step through tool calls, and replay conversations. The server supports hot-reloading. Code changes are reflected immediately.

> **Safari users:** Safari blocks localhost connections. Use `uv run langgraph dev --tunnel` instead.

> **Optional tracing:** To persist traces to LangSmith, add `LANGSMITH_API_KEY` to your `.env` (get one free at [smith.langchain.com/settings](https://smith.langchain.com/settings)).

### Option B: Standalone server (no Studio)

```bash
uv run python main.py
```

Starts the agent at `http://localhost:8123`. Use this mode when running alongside the UI.
