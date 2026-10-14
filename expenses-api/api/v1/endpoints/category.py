import logging
from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends

from api.deps import get_category_service
from core.auth import Principal
from core.security import check_scope, get_principal
from db.models import CategoryDB
from schemas import Category, CategoryCreate
from services import CategoryServices

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Category, tags=["Categories"])
async def create_category(
    category: CategoryCreate,
    principal: Principal = Depends(get_principal),
    category_services: CategoryServices = Depends(get_category_service),
) -> CategoryDB:
    check_scope(principal, "expenses:write")
    if principal.is_authenticated and principal.acting_user:
        logger.info("write sub=%s acting_user=%s", principal.sub, principal.acting_user)
    return await category_services.create_category(category=category)


@router.get("/", response_model=list[Category], tags=["Categories"])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    principal: Principal = Depends(get_principal),
    category_services: CategoryServices = Depends(get_category_service),
) -> Sequence[CategoryDB]:
    check_scope(principal, "expenses:read")
    return await category_services.read_categories(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=Category, tags=["Categories"])
async def read_category(
    category_id: UUID,
    principal: Principal = Depends(get_principal),
    category_services: CategoryServices = Depends(get_category_service),
) -> CategoryDB:
    check_scope(principal, "expenses:read")
    return await category_services.read_category(id=category_id)


@router.get("/name/{name}", response_model=Category, tags=["Categories"])
async def read_category_by_name(
    name: str,
    principal: Principal = Depends(get_principal),
    category_services: CategoryServices = Depends(get_category_service),
) -> CategoryDB:
    check_scope(principal, "expenses:read")
    return await category_services.read_category_by_name(name=name)
