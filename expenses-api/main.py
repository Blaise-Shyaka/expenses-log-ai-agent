from fastapi import FastAPI
from api.v1.endpoints.category import router as category_router
from api.v1.endpoints.expense import router as expense_router
import uvicorn
import os

app = FastAPI(title="Expenses Tracker API")

app.include_router(expense_router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(category_router, prefix="/api/v1/categories", tags=["Categories"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
