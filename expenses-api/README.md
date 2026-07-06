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

Then edit `.env`. Please replace the placeholder values with what you used above:

```
DATABASE_URL="mysql+aiomysql://dev_user:secret@localhost:3306/expenses_dev"
ALEMBIC_URL="mysql+pymysql://dev_user:secret@localhost:3306/expenses_dev"
```

> Both URLs point to the same database but use different drivers. `DATABASE_URL` uses `aiomysql` (async, for the app). `ALEMBIC_URL` uses `pymysql` (sync, for migrations). Both are required.

## 3. Install Dependencies

```bash
uv sync
```

## 4. Run Migrations

Wait ~10 seconds for MySQL to be ready, then:

```bash
uv run alembic upgrade head
```

This creates the tables and seeds a test user (`00000000-0000-0000-0000-000000000001`) used by all endpoints until authentication is implemented. This will change, as soon as the authentication is completed.

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

FastAPI generates interactive docs automatically. Once the server is running:

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
