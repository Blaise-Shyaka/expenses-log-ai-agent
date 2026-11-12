import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from agent.server import agent_lifespan, agent_status
from agent.server import router as agent_router
from api.v1.endpoints.category import router as category_router
from api.v1.endpoints.expense import router as expense_router
from config.db_config import app_settings
from core.security import enforce_auth
from exceptions.custom_exceptions import (
    AlreadyExistsException,
    NotFoundException,
    RepositoryException,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with agent_lifespan():
        yield


app = FastAPI(
    title="Expenses Tracker API",
    lifespan=lifespan,
    docs_url="/docs" if app_settings.DEBUG else None,
    redoc_url="/redoc" if app_settings.DEBUG else None,
    openapi_url="/openapi.json" if app_settings.DEBUG else None,
    dependencies=[Depends(enforce_auth)],
)


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(AlreadyExistsException)
async def already_exists_exception_handler(
    request: Request, exc: AlreadyExistsException
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(RepositoryException)
async def repository_exception_handler(request: Request, exc: RepositoryException) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(expense_router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(category_router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(agent_router, tags=["Agent"])


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "agent": agent_status()})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
