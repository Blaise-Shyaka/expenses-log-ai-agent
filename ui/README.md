# UI

Next.js chat interface powered by [CopilotKit](https://docs.copilotkit.ai). Talks to the Expenses Agent to log and query expenses via natural conversation.

## Prerequisites

- Node.js 18+
- pnpm
- [Expenses Agent](../expenses-agent/README.md). It should run at `AGENT_URL` that you'll pass in `.env`.

## 1. Configure Environment

```bash
cp .env.example .env
```

Set `AGENT_URL` to wherever your agent is running:

```
# Local agent
AGENT_URL=http://localhost:8123

# Hosted agent
AGENT_URL=https://agent.yourdomain.com
```

> This is the URL of the Expenses Agent. The UI proxies all chat messages through `/api/copilotkit` to this address.

## 2. Install Dependencies

```bash
npm install
```

## 3. Start the Dev Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
