# Expenses API

FastAPI REST API for storing and querying expenses. It uses Async SQLAlchemy + MySQL, and migrations via Alembic.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Docker — for running MySQL locally

## 1. Start MySQL

```bash
docker run --rm -d \
  --name expenses-db \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=expenses_dev \
  -e MYSQL_USER=dev_user \
  -e MYSQL_PASSWORD=secret \
  mysql:8
```

> **Note:** `--rm` removes the container when stopped. All data is lost on restart. Drop `--rm` if you want persistence between sessions.

## 2. Configure Environment

```bash
cp .env.example .env
```

Then edit `.env`. Replace the placeholder values with what you used above:

```
DATABASE_URL="mysql+aiomysql://dev_user:secret@localhost:3306/expenses_dev"
ALEMBIC_URL="mysql+pymysql://dev_user:secret@localhost:3306/expenses_dev"
```

> Both URLs point to the same database but use different drivers. `DATABASE_URL` uses `aiomysql` (async, for the app). `ALEMBIC_URL` uses `pymysql` (sync, for migrations). Both are required.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `MYSQL_ROOT_PASSWORD` | No | _(none)_ | Only used in the `docker run` command above to configure the local MySQL container — not read by the app itself. |
| `MYSQL_DATABASE` | No | _(none)_ | Same — Docker container config only. |
| `MYSQL_USER` | No | _(none)_ | Same — Docker container config only. |
| `MYSQL_PASSWORD` | No | _(none)_ | Same — Docker container config only. |
| `PORT` | No | `8000` | Port the API listens on (only applies when running via `python main.py`; `uvicorn --port` overrides it). |
| `DATABASE_URL` | **Yes** | `""` | Async MySQL DSN (`aiomysql`). Empty value fails at engine creation, so the app won't start without it. |
| `ALEMBIC_URL` | **Yes** | `""` | Sync MySQL DSN (`pymysql`) used only by `alembic upgrade`. Empty value fails migrations. |
| `AUTH_JWKS_URI` | Only if `AUTH_REQUIRED=true` | `""` | JWKS endpoint for RS256 JWT verification. Only fails once the first authenticated request comes in, not at startup. |
| `AUTH_ISSUER` | Only if `AUTH_REQUIRED=true` | `""` | Expected `iss` claim in inbound JWTs. |
| `AUTH_AUDIENCE` | No | `expenses-api` | Expected `aud` claim in inbound JWTs. |
| `AUTH_REQUIRED` | No | `true` | Set to `false` to bypass authentication in local development (all requests pass through unauthenticated). |
| `DEBUG` | No | `false` | Set to `true` to re-enable `/docs`, `/redoc`, and `/openapi.json`. |

## 3. Install Dependencies

```bash
uv sync
```

## 4. Run Migrations

Wait ~10 seconds for MySQL to be ready, then:

```bash
uv run alembic upgrade head
```

This creates the tables. A seed migration inserts a legacy test user row (`00000000-0000-0000-0000-000000000001`) that is preserved but no longer used by any endpoint.

## 5. Start the Server

```bash
uv run python main.py
```

For development with auto-reload:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now running at `http://localhost:8000`.

## Exploring the API

Interactive docs are disabled by default. Set `DEBUG=true` in `.env` and restart to enable:

| | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Raw OpenAPI JSON | http://localhost:8000/openapi.json |

### Import into Postman

1. Open Postman, then **Import**
2. Select **Link**, paste `http://localhost:8000/openapi.json`
3. All routes are imported with schemas and example bodies — no manual setup needed.

## API Routes

```
POST   /api/v1/expenses/                    Create expense (auto-creates category if missing)
GET    /api/v1/expenses/                    List expenses (skip/limit/category_name)
GET    /api/v1/expenses/{id}                Get single expense
GET    /api/v1/expenses/totals/by-category  Grouped totals by category
GET    /api/v1/expenses/totals/since        Total since date/days (optional category filter)

POST   /api/v1/categories/                  Create category
GET    /api/v1/categories/                  List categories
GET    /api/v1/categories/{id}              Get by UUID
GET    /api/v1/categories/name/{name}       Get by name (case-insensitive)
```
