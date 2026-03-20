#standard packages
from abc import ABC,abstractmethod
from typing import Generic,Type,TypeVar,Any,Sequence
from uuid import UUID

#third party packages
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError,SQLAlchemyError
from sqlalchemy import select


#local packages 
from ..base_class import Base
from exceptions.custom_exceptions import RepositoryException
from utils.logger_utils import logger



T=TypeVar('T',bound=Base)


#Implement a repository generic class
#Below is  an abstract class  that declares  must to have properties for each repository instance.

class GenericRepository(Generic[T],ABC):
  @abstractmethod 
  async def delete( self,id:UUID)->bool|None:
    raise NotImplementedError
  @abstractmethod
  async def read_all(self)->Sequence[T]:
    raise NotImplementedError
  @abstractmethod
  async def read_by_id(self,id:UUID)->T|None:
    raise NotImplementedError
  @abstractmethod
  async def update(self,obj:dict[str,Any],id:UUID)->T|None:
    raise NotImplementedError
  @abstractmethod
  async def create(self ,obj:T)->T|None:
     raise NotImplementedError


class GenericSqlRepository(GenericRepository[T]):
    
     def __init__(self,session:AsyncSession,model:Type[T]):
      self.session=session
      self.model=model

  # a method  to delete a database record by ID || think of a soft delete

     async def delete(self, id:UUID)->bool|None:
        try:
          db_obj= await self.session.get(self.model,id)
          if not db_obj:
            return False
          
          await self.session.delete(db_obj)
          await self.session.commit()
          return True
        except (DBAPIError,SQLAlchemyError) as exc:
           await self.session.rollback()
           self.handle_exception('delete',exc=exc)
             
     # a method to read a list of records from the database

     async def read_all(self,skip:int=0,limit:int=10):
       
       try:
         statement=select(self.model).offset(skip).limit(limit)
         results= await self.session.execute(statement)
         return results.scalars().all()
       except (DBAPIError,SQLAlchemyError)as exc:
          self.handle_exception('read_all',exc=exc)

# a method to read database record by Id
     async def read_by_id(self ,id:UUID):
       try:
          id_bytes=id.bytes
          result= await self.session.get(self.model,id_bytes)
          return result
          
       except (DBAPIError,SQLAlchemyError) as exc:
          self.handle_exception('reaby_by_id',exc=exc)

  # a method to update  a database  record by ID

     async def update(self,obj:dict[str,Any],id:UUID):
       try:
         db_obj= await self.read_by_id(id)
         if not db_obj:
           raise RepositoryException("Item not found")
         
         for key,value in obj.items():
           if key.startswith('__'):
             continue
           setattr(db_obj,key,value)

           await self.session.commit() 
           await self.session.refresh(db_obj)
           return db_obj
             
       except (DBAPIError,SQLAlchemyError)as exc:
          await self.session.rollback()
          self.handle_exception("update",exc=exc)

     async def create(self, obj:T)->T|None:
       try:
          self.session.add(obj)
          await self.session.commit()
          await self.session.refresh(obj)
          return obj
        
       except (DBAPIError,SQLAlchemyError)as exc:
          await self.session.rollback()
          self.handle_exception('create',exc=exc)

  
     def handle_exception(self,operation:str,exc:Exception):
      
       logger.error(f"Repository exception during:{operation}:{exc}",exc_info=True,extra={"model":f"{self.model.__name__}"})
       raise RepositoryException(f"Repository Error during :{operation}")