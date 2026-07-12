from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from core.constants import TEST_USER_ID_BYTES
from db.models import CategoryDB
from schemas.schema import Category, CategoryCreate

router = APIRouter()


@router.post("/", response_model=Category, tags=["Categories"])
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category_stmt = select(CategoryDB).where(func.lower(CategoryDB.name) == category.name.lower())
    result = await db.execute(category_stmt)
    category_exists = result.scalars().first()
    if category_exists:
        raise HTTPException(status_code=400, detail="Category already exists")

    category.name = category.name.lower()
    # TODO: Replace TEST_USER_ID_BYTES with authenticated user's ID
    db_category = CategoryDB(**category.model_dump(), user_id=TEST_USER_ID_BYTES)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.get("/", response_model=list[Category], tags=["Categories"])
async def read_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # TODO: Try to handle pagination in a much better way
    categories_stmt = select(CategoryDB).offset(skip).limit(limit)
    result = await db.execute(categories_stmt)
    return result.scalars().all()


@router.get("/{category_id}", response_model=Category, tags=["Categories"])
async def read_category(category_id: UUID, db: AsyncSession = Depends(get_db)):
    category_stmt = select(CategoryDB).where(CategoryDB.id == category_id.bytes)
    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.get("/name/{name}", response_model=Category, tags=["Categories"])
async def read_category_by_name(name: str, db: AsyncSession = Depends(get_db)):
    category_stmt = select(CategoryDB).where(func.lower(CategoryDB.name) == name.lower())
    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category
