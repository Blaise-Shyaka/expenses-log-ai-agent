# expenses-log-ai-agent

Track your personal expenses by simply talking to an AI. Paste a payment confirmation, and watch it log itself.

**ExpenseLog is live at [expenselog.uk](https://expenselog.uk/).** Create an account and paste your first payment confirmation.

Chat interactions happen through a [CopilotKit](https://docs.copilotkit.ai) interface that routes messages to a LangGraph agent. The agent calls tools exposed by an MCP server, which records expenses via a REST API.

## Motivation

Logging personal expenses with traditional apps feels like a chore or administration work.

Most expense trackers are built for corporate reimbursement: complex setup, mandatory mobile apps, manual data entry, and constant categorizing. That's fine for work trips. But for tracking personal finances, it's exhausting.

We take a different approach. Instead of fighting an app, just *talk* to it. Paste a payment confirmation from SMS or email, and let the AI do the rest. It extracts the details, suggests a category, and logs it. That's it.

No forms. No friction. Just expenses, effortlessly tracked.

## How It Works

Expenses are grouped in categories. Each category has a description that helps the LLM understand how to classify expenses. For instance, a `utility` category might have a description like: *"Utilities category will contain exclusively utility-related expenses: water, electricity, gas, internet, and phone bills."*

There are already default categories, but you can edit or add more. If you'd prefer "Water" as its own category instead of lumped under utilities, just change it by talking to the agent. Add new categories, provide a description, and the AI will start using them.

## Features

1. Log expense entries from natural language or pasted confirmations
2. Create and manage expense categories with custom descriptions
3. Get expense reports by category, timeline, or specific time period

## Architecture

The agent now runs inside `expenses-api` at `/agent`. Each service has its own README:

| Service | Description | README |
|---|---|---|
| **expenses-auth** | Go service that issues and verifies JWTs (user login + service-to-service tokens) | [README](./expenses-auth/README.md) |
| **expenses-api** | FastAPI app: the REST API that stores and queries expenses via MySQL (`/api/v1`) and the LangGraph agent that understands messages and calls MCP tools (`/agent`) | [README](./expenses-api/README.md) |
| **expenses-mcp** | MCP server that exposes expense tools to the agent | [README](./expenses-mcp/README.md) |
| **expenses-agent** | The standalone agent, still deployed until the UI is switched to `/agent` (#63). Frozen: make agent changes in `expenses-api/agent/` | [README](./expenses-agent/README.md) |
| **ui** | Next.js chat interface powered by CopilotKit | [README](./ui/README.md) |

### Request Flow

```
User visits UI, not yet logged in
      │
      ▼
  UI (port 3000)
  Next.js proxy (proxy.ts) redirects to /login
      │  POST AUTH_SERVICE_URL/login
      ▼
  expenses-auth (port 8001)
  verifies credentials, issues JWT access + refresh tokens
      │  tokens stored in an encrypted httpOnly cookie (Auth.js)
      ▼
  User types message
      │
      ▼
  UI (port 3000)
  CopilotChat component
      │  POST /api/copilotkit  (browser attaches Bearer access token)
      ▼
  UI route handler
  proxies AG-UI streaming request
      │  POST /agent (AG-UI protocol, Authorization: Bearer <jwt>)
      ▼
  Expenses API, agent route (port 8000)
  verifies JWT against Auth Service JWKS, then:
  LangGraph: llm_node → [tool call?] → llm_node
      │  executes tool (loaded from MCP at startup), attaches its own service token
      ▼
  Tool makes HTTP call
      │  POST /mcp (Authorization: Bearer <service token>, X-Acting-User: <user id>)
      ▼
  Expenses MCP (port 8124)
  verifies JWT against Auth Service JWKS, resolves acting user, then:
      │  HTTP to /api/v1/... (Authorization: Bearer <service token>)
      ▼
  Expenses API (port 8000)
  verifies JWT against Auth Service JWKS, scopes query to acting user
      │  async SQLAlchemy
      ▼
  MySQL (port 3306)
  users, categories, expenses tables
      │
      ▼
  Response flows back up the chain
  Agent replies in natural language
```

> **Note on MCP:** The agent loads its tool definitions from the MCP server (`expenses-mcp`, port 8124) once at startup. After that, every tool call is a network round trip: the agent calls `expenses-mcp` over HTTP, which calls back into `expenses-api`'s `/api/v1` over HTTP.

> **Note on auth:** `expenses-api` (for both `/api/v1` and `/agent`) and `expenses-mcp` each accept `AUTH_REQUIRED=false`, which skips checking incoming tokens in that service only. `expenses-auth` must still run, because the agent and the MCP server fetch their service tokens from it, and the MCP tools fail without a verified token. The UI has no bypass for the login redirect.

The agent can use either [DeepSeek](https://platform.deepseek.com) (cloud) or [Ollama](https://ollama.com) (local) as its LLM, controlled by a single environment variable.

## Running Locally

Clone the repo:

```bash
git clone https://github.com/Blaise-Shyaka/expenses-log-ai-agent.git
cd expenses-log-ai-agent
```

Then follow each service's README in order:

1. [expenses-auth](./expenses-auth/README.md) — start the auth service first; the agent, the MCP server and the UI need it even with `AUTH_REQUIRED=false`
2. [expenses-api](./expenses-api/README.md) — start MySQL and the app (REST API and agent); the agent loads in the background once the MCP server is up
3. [expenses-mcp](./expenses-mcp/README.md) — start the MCP tool server (depends on the API)
4. [ui](./ui/README.md) — start the chat interface last
