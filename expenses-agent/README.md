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
