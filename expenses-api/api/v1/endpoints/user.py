#standard  packages
from uuid import UUID
from typing import Annotated

#third party packages
from fastapi import APIRouter,Body,Depends

#local packages 
from schemas import UserCreate,User
from services import UserServices
from api.deps import get_user_services


router=APIRouter()

@router.post('/',response_model=User,tags=["Users"])
async def create_user(user:Annotated[UserCreate,Body()],user_services:Annotated[UserServices,Depends(get_user_services)]):
    new_user= await user_services.create_user(user=user)
    return new_user

@router.get('/{user_id}',response_model=User,tags=["Users"])
async def read_user_by_id(user_id:UUID,user_services:Annotated[UserServices,Depends(get_user_services)]):
    user= await user_services.read_user_by_id(id=user_id)
    return user

@router.get('/',response_model=list[User],tags=["Users"])
async def read_users(user_services:Annotated[UserServices,Depends(get_user_services)],limit:int=10,skip:int=0,):
    users= await user_services.read_users(limit=limit,skip=skip)
    return users