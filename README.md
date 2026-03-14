# momo-expenses-langraph-ai-agent

This is an AI-assistant that lets you log expenses using natural language or voice.

Chat interactions are triggered from an MCP client built with copilot-kit, communicating with an MCP server that orchestrates tool calls via Gemini-powered LangGraph.

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

## Current Architecture

The project currently consists of:
- **Expenses Agent**: LangGraph-powered agent for expense tracking using Gemini
- **Expenses API**: FastAPI backend for expense management
- **UI**: CopilotKit Assistant UI for chat interactions
