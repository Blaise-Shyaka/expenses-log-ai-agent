# expenses-log-ai-agent

Track your personal expenses by simply talking to an AI. Paste a payment confirmation, and watch it log itself.

**[Try the live demo](http://dywm0f0jdse5uuzns55y6avz.161.97.78.63.sslip.io/)**

Chat interactions happen through a [CopilotKit](https://docs.copilotkit.ai) interface that routes messages to a LangGraph agent. The agent extracts expense details, picks a category, and records them via a REST API. An MCP server integration is in the works (coming soon).

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

Three services, each with its own README:

| Service | Description | README |
|---|---|---|
| **expenses-api** | FastAPI REST API that stores and queries expenses via MySQL | [README](./expenses-api/README.md) |
| **expenses-agent** | LangGraph AI agent that understands messages, calls tools, and records expenses | [README](./expenses-agent/README.md) |
| **ui** | Next.js chat interface powered by CopilotKit | [README](./ui/README.md) |

### Request Flow

```
User types message
      │
      ▼
  UI (port 3000)
  CopilotChat component
      │  POST /api/copilotkit
      ▼
  Expenses Agent (port 8123)
  LangGraph graph: llm_node → tools → llm_node
      │  LLM decides which tool to call
      ▼
  Expenses API (port 8000)
  FastAPI REST endpoints
      │  async SQLAlchemy
      ▼
  MySQL (port 3306)
  expenses, categories, users tables
      │
      ▼
  Response flows back up the chain
  Agent replies in natural language
```

The agent can use either [DeepSeek](https://platform.deepseek.com) (cloud) or [Ollama](https://ollama.com) (local) as its LLM, controlled by a single environment variable.

## Running Locally

Clone the repo:

```bash
git clone https://github.com/Blaise-Shyaka/expenses-log-ai-agent.git
cd expenses-log-ai-agent
```

Then follow each service's README in order:

1. [expenses-api](./expenses-api/README.md); start MySQL and the REST API first
2. [expenses-agent](./expenses-agent/README.md); start the agent (depends on the API)
3. [ui](./ui/README.md); start the chat interface last
