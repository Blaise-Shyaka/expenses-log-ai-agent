# UI

Next.js chat interface powered by [CopilotKit](https://docs.copilotkit.ai). Talks to the agent at the app's `/agent` route to log and query expenses via natural conversation.

## Prerequisites

- Node.js 18+
- pnpm
- [expenses-api](../expenses-api/README.md), which serves the agent at `/agent`. Pass that URL as `AGENT_URL` in `.env`.

## 1. Configure Environment

```bash
cp .env.example .env
```

Set the required variables:

```
AGENT_URL=http://localhost:8000/agent  # the agent route on expenses-api
AUTH_SERVICE_URL=http://localhost:8001  # URL of the Go auth service
AUTH_SECRET=<generated-secret>       # Cookie-encryption secret for Auth.js
```

Generate `AUTH_SECRET`:

```bash
npx auth secret
```

> `AUTH_SECRET` is used by Auth.js to encrypt the httpOnly session cookie. It never leaves the server. Rotate it to invalidate all existing sessions.

## Auth flow

1. Unauthenticated visitors are redirected to `/login` by the Next.js middleware.
2. The login form calls `POST /api/auth/[...nextauth]` (Auth.js) server-side, which exchanges credentials with the Go auth service (`POST AUTH_SERVICE_URL/login`) and stores the resulting JWT pair in an encrypted httpOnly cookie — the browser never sees a raw token.
3. On subsequent requests the Auth.js `jwt` callback transparently refreshes expired tokens via `POST AUTH_SERVICE_URL/oauth/token` (refresh_token grant) before handing control back.

> **Naming note:** the expenses-auth base URL is deliberately `AUTH_SERVICE_URL`, not `AUTH_URL`. Auth.js v5 reserves `AUTH_URL` for itself (it overrides the app's own canonical origin when set — see `next-auth/lib/env.js`), so reusing that name here would make Auth.js think the UI app itself lives at the expenses-auth's address, sending all its internal redirects there instead.
4. Every chat request to `/api/copilotkit` reads the session server-side, injects a fresh `Authorization: Bearer <access_token>` header onto the inbound request, and lets the CopilotKit runtime forward it to the agent — no client-side token exposure.

## 2. Install Dependencies

```bash
pnpm install
```

## 3. Start the Dev Server

```bash
pnpm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Production

The production build (`NODE_ENV=production`, as in the Dockerfile) marks its auth cookies `Secure`, so browsers only send them over HTTPS. Serve it behind HTTPS with HTTP redirected to HTTPS; over plain HTTP, sign-in will not stick. `http://localhost` still works, because browsers treat it as secure.
