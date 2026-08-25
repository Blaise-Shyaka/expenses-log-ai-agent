import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from core.auth import Principal
from core.provisioning import ensure_user
from core.security import check_scope, get_principal
from db.models import CategoryDB
from schemas.schema import Category, CategoryCreate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Category, tags=["Categories"])
async def create_category(
    category: CategoryCreate,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> CategoryDB:
    check_scope(principal, "expenses:write")

    if principal.is_authenticated and principal.acting_user:
        await ensure_user(db, principal.acting_user)
        logger.info("write sub=%s acting_user=%s", principal.sub, principal.acting_user)

    user_bytes = UUID(principal.acting_user).bytes if principal.acting_user else b""

    category_stmt = select(CategoryDB).where(func.lower(CategoryDB.name) == category.name.lower())
    if principal.acting_user:
        category_stmt = category_stmt.where(CategoryDB.user_id == user_bytes)

    result = await db.execute(category_stmt)
    category_exists = result.scalars().first()
    if category_exists:
        raise HTTPException(status_code=400, detail="Category already exists")

    category.name = category.name.lower()
    db_category = CategoryDB(**category.model_dump(), user_id=user_bytes)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.get("/", response_model=list[Category], tags=["Categories"])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryDB]:
    check_scope(principal, "expenses:read")

    categories_stmt = select(CategoryDB).offset(skip).limit(limit)
    if principal.is_authenticated and principal.acting_user:
        categories_stmt = categories_stmt.where(
            CategoryDB.user_id == UUID(principal.acting_user).bytes
        )

    result = await db.execute(categories_stmt)
    return list(result.scalars().all())


@router.get("/{category_id}", response_model=Category, tags=["Categories"])
async def read_category(
    category_id: UUID,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> CategoryDB:
    check_scope(principal, "expenses:read")

    category_stmt = select(CategoryDB).where(CategoryDB.id == category_id.bytes)
    if principal.is_authenticated and principal.acting_user:
        category_stmt = category_stmt.where(CategoryDB.user_id == UUID(principal.acting_user).bytes)

    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.get("/name/{name}", response_model=Category, tags=["Categories"])
async def read_category_by_name(
    name: str,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> CategoryDB:
    check_scope(principal, "expenses:read")

    category_stmt = select(CategoryDB).where(func.lower(CategoryDB.name) == name.lower())
    if principal.is_authenticated and principal.acting_user:
        category_stmt = category_stmt.where(CategoryDB.user_id == UUID(principal.acting_user).bytes)

    result = await db.execute(category_stmt)
    db_category = result.scalars().first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category
