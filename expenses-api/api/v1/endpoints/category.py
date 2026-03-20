#standard packages
from typing import List
from uuid import UUID

#third party packages
from fastapi import APIRouter, Depends

#local packages
from schemas import Category, CategoryCreate
from api.deps import get_category_service
from services import CategoryServices

router = APIRouter()

@router.post("/", response_model=Category, tags=["Categories"])
async def create_category(category: CategoryCreate, category_services:CategoryServices=Depends(get_category_service)):
    return await category_services.create_category(category=category)

   
@router.get("/", response_model=List[Category], tags=["Categories"])
async def read_categories(skip: int = 0, limit: int = 100,category_services:CategoryServices=Depends(get_category_service)):
    #  TODO: Try to handle pagination in a much better way
    return await category_services.read_categories(skip=skip,limit=limit)


@router.get("/{category_id}", response_model=Category, tags=["Categories"])
async def read_category(category_id: UUID, category_services:CategoryServices=Depends(get_category_service)):
    return await category_services.read_category(id=category_id)


@router.get("/name/{name}", response_model=Category, tags=["Categories"])
async def read_category_by_name(name: str, category_services:CategoryServices=Depends(get_category_service)):
    return await category_services.read_category_by_name(name=name)
