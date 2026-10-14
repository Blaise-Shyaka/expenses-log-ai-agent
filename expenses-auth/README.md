# expenses-auth

Standalone Go authentication service. Port 8001.

## Environment

Copy `.env.example` to `.env` and fill in values:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8001` | HTTP listen port |
| `DATABASE_URL` | _(none)_ | PostgreSQL DSN. If unset, uses in-memory store (no persistence). |
| `SIGNING_KEY_PATH` | `signing.key` | Path for RSA private key. Generated on first run if missing. Ignored if `SIGNING_KEY_PEM` is set. |
| `SIGNING_KEY_PEM` | _(none)_ | PEM-encoded RSA private key, supplied directly (e.g. from a secrets manager). Takes precedence over `SIGNING_KEY_PATH` and never touches disk. Literal `\n` sequences are accepted in place of real newlines. |
| `ISSUER_URL` | `http://localhost:8001` | JWT `iss` claim value. |
| `SVC_AGENT_SECRET` | _(none)_ | Secret for machine client `svc-agent`. Both SVC_* vars must be set to seed clients. |
| `SVC_MCP_SECRET` | _(none)_ | Secret for machine client `svc-mcp`. |
| `SEED_DEV_USER` | `false` | Set to `true` to seed dev user `00000000-0000-0000-0000-000000000001`. |

## Run

```bash
cp .env.example .env
# edit .env

go run . 
```

With Postgres running:
```bash
DATABASE_URL=postgres://user:pass@localhost:5432/auth_db?sslmode=disable go run .
```

The service auto-runs `CREATE TABLE IF NOT EXISTS` migrations on startup when `DATABASE_URL` is set.

## Test

```bash
go test ./...
go vet ./...
```

No live Postgres required — tests use the in-memory store.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/.well-known/jwks.json` | Public key set for JWT verification |
| `POST` | `/register` | Register a user |
| `POST` | `/login` | Login, receive access + refresh tokens |
| `POST` | `/oauth/token` | Token endpoint: `client_credentials` and `refresh_token` grants |

### POST /register

```json
{ "email": "user@example.com", "password": "...", "first_name": "Alice", "last_name": "Smith" }
```

Returns `201 { "id": "<uuid>", "email": "..." }` or `409` on duplicate email.

### POST /login

```json
{ "email": "user@example.com", "password": "..." }
```

Returns `200 { "access_token": "<jwt>", "refresh_token": "<opaque>", "expires_in": 900 }` or `401` on failure.

### POST /oauth/token — client_credentials

Form-encoded body (or HTTP Basic auth for client_id/client_secret):

```
grant_type=client_credentials&client_id=svc-agent&client_secret=<secret>
```

Returns `200 { "access_token": "<jwt>", "token_type": "Bearer", "expires_in": 900 }`.

JWT claims: `sub`=client_id, `aud`=client audience, `scope`=client scopes, `token_type`="service".

No `refresh_token` issued (standard OAuth2 behavior for client_credentials).

Wrong client_id or secret → `401`.

### POST /oauth/token — refresh_token

Form-encoded body:

```
grant_type=refresh_token&refresh_token=<opaque>
```

Returns `200 { "access_token": "<jwt>", "refresh_token": "<new_opaque>", "token_type": "Bearer", "expires_in": 900 }`.

Tokens are rotated on each use. Reusing an already-rotated token → `401`.

### Seeded machine clients

When both `SVC_AGENT_SECRET` and `SVC_MCP_SECRET` are set, two clients are created at startup (idempotent):

| client_id | audience | scopes |
|---|---|---|
| `svc-agent` | `expenses-mcp` | `mcp:call act-on-behalf` |
| `svc-mcp` | `expenses-api` | `expenses:read expenses:write act-on-behalf` |
