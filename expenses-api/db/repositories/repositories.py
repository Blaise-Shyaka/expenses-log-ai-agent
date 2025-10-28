#standard packages
from uuid import UUID
from datetime import datetime

#third party packages
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError,SQLAlchemyError
from sqlalchemy import select,func
from sqlalchemy.orm import selectinload

#local packages
from .base_repository import GenericSqlRepository
from ..models import CategoryDB,ExpenseDB,UserDB

class Repo:
  def __init__(self,session:AsyncSession):
    ...

class CategoryRepository(GenericSqlRepository[CategoryDB],Repo):
    def __init__(self,session:AsyncSession):
        super().__init__(session=session,model=CategoryDB)

    async def read_by_name(self,name:str)->CategoryDB|None:
        try:
         statement=select(self.model).where(func.lower(CategoryDB.name) ==name.lower())
         results= await self.session.execute(statement)
         return results.scalars().first()
        except (DBAPIError,SQLAlchemyError) as exc:
           self.handle_exception('read_by_name',exc=exc) 
          

class ExpensesRepository(GenericSqlRepository[ExpenseDB],Repo):
    def __init__(self,session:AsyncSession):
       super().__init__(session=session,model=ExpenseDB)

    async def read_by_id(self, id: UUID):
       try:
         id_bytes=id.bytes
         statement=select(self.model).options(selectinload(self.model.category)).where(self.model.id==id_bytes)
         results= await self.session.execute(statement)
         return results.scalars().first()
       except (DBAPIError,SQLAlchemyError) as exc:
          self.handle_exception('read_by_id',exc=exc)

    async def read_all(self,skip:int=0,limit:int=10,category_name:str|None=None):
       try:
          statememt=select(self.model).options(selectinload(self.model.category)).limit(limit).offset(skip)
          if category_name is not None:
             statememt=statememt.join(CategoryDB).filter(func.lower(CategoryDB.name) == category_name.lower())
          results = await self.session.execute(statememt)
          return results.scalars().all()
       

       except (DBAPIError,SQLAlchemyError) as exc :
           self.handle_exception('read_all',exc=exc)
   
    async def read_total_by_category(self,category_name:str|None=None):
       try :
          statement = select(CategoryDB, func.sum(ExpenseDB.amount).label("total_expenses")).join(ExpenseDB, CategoryDB.id == ExpenseDB.category_id).group_by(CategoryDB.id)

          if category_name:
             statement=statement.filter(func.lower(CategoryDB.name)==category_name.lower())
             
          results= await self.session.execute(statement)
          return results.all()
       
       except (DBAPIError,SQLAlchemyError) as exc:
          self.handle_exception('read_totals_by_category',exc=exc)

    
    async def read_totals_since(self,start_date:datetime,category_name:str|None=None):
       try :
          statement=select(func.sum(self.model.amount).label('total')).where(ExpenseDB.date>=start_date)
          if category_name:
              statement=statement.join(CategoryDB).group_by(CategoryDB.name).where(func.lower(CategoryDB.name) == category_name.lower())

          result=await self.session.execute(statement)
          return result.scalar() or 0.0
       except (DBAPIError,SQLAlchemyError) as exc:
          self.handle_exception('read_totals_since',exc=exc)
    
class UsersRepository(GenericSqlRepository[UserDB],Repo):
   def __init__(self,session:AsyncSession):
      super().__init__(session=session,model=UserDB)
   
   async def read_by_email(self,email:str):
      try:
         statement=select(self.model).where(self.model.email==email)
         result=await self.session.execute(statement)
         return result.first()
      except (DBAPIError,SQLAlchemyError)as exec:
         self.handle_exception("read_by_email",exc=exec)