import os

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from api.v1.endpoints.category import router as category_router
from api.v1.endpoints.expense import router as expense_router
from config.db_config import app_settings
from core.security import enforce_auth

app = FastAPI(
    title="Expenses Tracker API",
    docs_url="/docs" if app_settings.DEBUG else None,
    redoc_url="/redoc" if app_settings.DEBUG else None,
    openapi_url="/openapi.json" if app_settings.DEBUG else None,
    dependencies=[Depends(enforce_auth)],
)

app.include_router(expense_router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(category_router, prefix="/api/v1/categories", tags=["Categories"])


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
