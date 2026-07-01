# momo-expenses-langraph-ai-agent

Track your personal expenses by simply talking to an AI. Paste a payment confirmation, and watch it log itself.

Chat interactions are triggered from an MCP client built with CopilotKit, communicating with an MCP server that orchestrates tool calls via an LLM-powered LangGraph agent.

## Motivation

Logging personal expenses with traditional apps feels like a chore or administration work.

Most expense trackers are built for corporate reimbursement—complex setup, mandatory mobile apps, manual data entry, and constant categorizing. That's fine for work trips. But for tracking personal finances, it's exhausting.

We take a different approach. Instead of fighting an app, just *talk* to it. Paste a payment confirmation from SMS or email, and let the AI do the rest. It extracts the details, suggests a category, and logs it. That's it.

No forms. No friction. Just expenses, effortlessly tracked.

## How It Works

Expenses are grouped in categories. Each category has a description that helps the LLM understand how to classify expenses. For instance, a `utility` category might have a description like: *"Utilities category will contain exclusively utility-related expenses: water, electricity, gas, internet, and phone bills."*

There are already default categories, but you can edit or add more. If you'd prefer "Water" as its own category instead of lumped under utilities, just change it. Add new categories, provide a description, and the AI will start using them.

## Features

1. Create, edit, and delete expense entries
2. Create, edit, and delete categories
3. Get expense reports by category, timeline, or specific time period

## Architecture

The project consists of three main components:

- **Expenses Agent**: LangGraph-powered AI agent for understanding and categorizing expenses (uses Gemini or Ollama)
- **Expenses API**: FastAPI backend handling data persistence and retrieval
- **UI**: CopilotKit-powered chat interface for natural conversation

## 🚀 Running the Project Locally

Follow these steps to run the project on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/Blaise-Shyaka/momo-expenses-langraph-ai-agent.git
cd momo-expenses-langraph-ai-agent
```

### 2. Set Up Environment Variables

Each of the following directories contains an `.env.example` file:

* `expenses-agent`
* `expenses-api`
* `ui`

For each of them:

```bash
cd <directory-name>
cp .env.example .env
# Edit the .env file to update values as needed
```

### 3. Start the Backend Services

Back in the project root directory, start the backend services:

```bash
docker compose up --build
```

This starts the API, Agent, and MySQL database.

### 3.1 Run Ollama Locally (optional)

If `USE_LOCAL_MODEL=true` in your `.env`, run Ollama via Docker:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3.2
```

### 4. Start the UI (separate terminal)

In a new terminal, run the UI locally for faster development:

```bash
cd ui
npm install
npm run dev
```

### 5. Access the App

Once everything is running, open your browser and navigate to:

[http://localhost:3000](http://localhost:3000)
