#standard packages
from typing import Type,TypeVar

#third party packages
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

#local packages 
from db.session import SessionLocal
from db.repositories.repositories import Repo,CategoryRepository,ExpensesRepository,UsersRepository
from services.services import CategoryServices,ExpensesServices,UserServices

T=TypeVar('T',bound=Repo)

# dependencies should not be coroutines
async def get_db():
  async with SessionLocal() as db:
    try:
      yield db
    finally:
      await db.close()

def get_repo(cls:Type[T]):
    def _get_repo(session:AsyncSession=Depends(get_db))->T:
      return cls(session=session)
    return _get_repo

def get_category_service(repo:CategoryRepository=Depends(get_repo(CategoryRepository))):
     return CategoryServices(repo)

def get_expenses_service(category_repo:CategoryRepository=Depends(get_repo(CategoryRepository)),expenses_repo:ExpensesRepository=Depends(get_repo(ExpensesRepository))):
     return ExpensesServices(category_repo=category_repo,expenses_repo=expenses_repo)

def get_user_services(user_repo:UsersRepository=Depends(get_repo(UsersRepository))):
     return UserServices(user_repository=user_repo)