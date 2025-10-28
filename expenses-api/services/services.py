#standard libray
from uuid import UUID
from datetime import datetime,timedelta

#third party packages
from fastapi import HTTPException,status

#local packages
from db.repositories import CategoryRepository,ExpensesRepository,UsersRepository
from db.models import CategoryDB,ExpenseDB,UserDB
from schemas import CategoryCreate,ExpenseCreate,ExpenseTotalResponse,CategoryWithTotal,User,ExpenseWithCategory,UserCreate
from core.constants import TEST_USER_ID_BYTES
from schemas import  Expense
from utils import ensure_uuid_value
from utils import generate_hash

class CategoryServices:
    def __init__(self,repo:CategoryRepository):
        self.category_repository=repo
    async def read_category(self,id:UUID)->CategoryDB|None:
           db_category= await self.category_repository.read_by_id(id=id)
           if not db_category :
                raise HTTPException(detail="Not found",
                                    status_code=status.HTTP_404_NOT_FOUND)
           return db_category
    
     
    async def read_category_by_name(self,name:str)->CategoryDB|None:
           db_category= await self.category_repository.read_by_name(name=name)
           if not db_category :
                 raise HTTPException(detail="Not found",
                                    status_code=status.HTTP_404_NOT_FOUND)
           return db_category
    
    async def read_categories(self,skip:int=0,limit:int=10):
           return await self.category_repository.read_all(skip=skip,limit=limit)
    

    async def create_category(self,category:CategoryCreate)->CategoryDB|None:
              category_exists= await self.category_repository.read_by_name(name=category.name)
              if category_exists:
                raise HTTPException(detail="Category already exists",
                                    status_code=status.HTTP_400_BAD_REQUEST)

              category.name=category.name.lower()
              new_category=CategoryDB(**category.model_dump(),user_id=TEST_USER_ID_BYTES)
              return await self.category_repository.create(new_category)

class ExpensesServices:
      def __init__(self,category_repo:CategoryRepository,expenses_repo:ExpensesRepository) -> None:
            self.expenses_repository=expenses_repo
            self.categories_repository=category_repo

      async def create_expense(self,expense:ExpenseCreate):
            db_category=await self.categories_repository.read_by_name(expense.category_name.lower())

            if db_category is None:
                  new_category=CategoryDB(name=expense.category_name,user_id=TEST_USER_ID_BYTES)
                  db_category =await self.categories_repository.create(new_category)

            if db_category  is None:
                        return None
            db_expense=ExpenseDB(
                            amount=expense.amount,
                            date=expense.date,
                            description=expense.description,
                            category_id=db_category.id,
                            user_id=TEST_USER_ID_BYTES
                        )
                       
            result=await self.expenses_repository.create(db_expense)
            if result :
                  return Expense(amount=result.amount,description=result.description,category_id=UUID(bytes=result.category_id) if isinstance(result.category_id,bytes) else result.category_id,id=UUID(bytes=result.id) if isinstance(result.id,bytes) else result.id)
          
            return None

      async def read_expenses(self,category_name:str|None=None,skip:int=0,limit:int=10):
      
              if category_name is not None:
                    category_exists= await self.categories_repository.read_by_name(name=category_name)
                    if not category_exists:
                         raise HTTPException(detail="Category not found",
                                    status_code=status.HTTP_404_NOT_FOUND)  
                    
              results= await self.expenses_repository.read_all(category_name=category_name,skip=skip,limit=limit)
            
              return [ExpenseWithCategory(
                    id=ensure_uuid_value(expense.id),
                    amount=expense.amount,
                    category_id=expense.category_id,
                    category=expense.category,
                    description=expense.description
              )for expense in results]
      
      async def read_totals_by_category(self,category_name:str|None=None)->list[CategoryWithTotal]:
               results=await self.expenses_repository.read_total_by_category(category_name=category_name)
               return [CategoryWithTotal(
                      id=ensure_uuid_value(category.id),name=category.name,
                      description=category.description,
                      total_expenses=total
               ) for category,total  in list(results)]
      
      async def read_totals_since(self,start_date:datetime|None=None,days:int|None=None,category_name:str|None=None)->ExpenseTotalResponse:
       
              if days is not None and start_date is None:
                    start_date=datetime.now()-timedelta(days=days)
              elif start_date is None:
                    # Default to last 30 days if neither is provided
                    days=30
                    start_date=datetime.now()- timedelta(days=days)
              total= await self.expenses_repository.read_totals_since(start_date=start_date,category_name=category_name)
              
              return ExpenseTotalResponse(
                    total=total,
                    start_date=start_date,
                    days=days,
                    category_name=category_name or "all"
              )
      async def read_by_id(self,id:UUID):
            db_expense=await self.expenses_repository.read_by_id(id=id)

            if not db_expense:
                   raise HTTPException(detail="Expense not found",
                                    status_code=status.HTTP_404_NOT_FOUND)
            return db_expense

class UserServices:
       def __init__(self,user_repository:UsersRepository) -> None:
              self.repository=user_repository

       async def read_users(self,limit:int=10,skip:int=0):
              
        results=await self.repository.read_all(skip=skip,limit=limit)
        return [
                  User(
                        id=ensure_uuid_value(user.id),
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email
                      ) for user in results
              ]
       async def read_user_by_id(self,id:UUID):
             user=await self.repository.read_by_id(id);
             if not user:
                    raise HTTPException(detail="User Not found",
                                    status_code=status.HTTP_404_NOT_FOUND)
             return user
       
       async def create_user(self,user:UserCreate):
             user_exists= await self.repository.read_by_email(email=user.email)

             if user_exists:
                   raise HTTPException(detail="User already exists",status_code=status.HTTP_409_CONFLICT)

             db_user=UserDB(
                   first_name=user.first_name,
                   last_name=user.last_name,
                   email=user.email,
             )

             if user.password:
                   #hash the password as bytes then store it as  hashed text
                   db_user.hashed_password=generate_hash(user.password.encode('utf-8')).decode('utf-8')

             new_user= await self.repository.create(db_user)

             return new_user