from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1 import deps
from app.api.v1.schemas.category import CategoryResponse
from app.db.repositories.category_repository import CategoryRepository


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    category_repo: CategoryRepository = Depends(deps.get_category_repository),
) -> list[CategoryResponse]:
    categories = category_repo.list_all()
    return [CategoryResponse.from_orm(category) for category in categories]
