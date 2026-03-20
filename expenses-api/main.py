from fastapi import FastAPI,Request
from api.v1.endpoints import category, expense,user
from exceptions.custom_exceptions import RepositoryException
from fastapi.responses import JSONResponse

app = FastAPI(title="Expenses Tracker API")

# Repository Exception handler

@app.exception_handler(RepositoryException)
async def repository_exception_handler(request:Request,exc:RepositoryException):
    return JSONResponse(
        status_code=500,
        content={"message":f"Internal server exception happened :{exc}"}
    )
app.include_router(expense.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(category.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(user.router,prefix="/api/v1/users",tags=["Users"])
