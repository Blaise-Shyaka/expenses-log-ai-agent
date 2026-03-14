from fastapi import FastAPI
from api.v1.endpoints.category import router as category_router
from api.v1.endpoints.expense import router as expense_router

app = FastAPI(title="Expenses Tracker API")

app.include_router(expense_router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(category_router, prefix="/api/v1/categories", tags=["Categories"])
