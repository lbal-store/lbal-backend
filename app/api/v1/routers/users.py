from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1 import deps
from app.api.v1.schemas.user import UserMeResponse, UserPublicProfileResponse, UserUpdateRequest
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
def read_current_user(current_user: User = Depends(deps.get_current_user)) -> UserMeResponse:
    return UserMeResponse.from_orm(current_user)


@router.put("/me", response_model=UserMeResponse)
def update_current_user(
    payload: UserUpdateRequest,
    current_user: User = Depends(deps.get_current_user),
    user_repo: UserRepository = Depends(deps.get_user_repository),
) -> UserMeResponse:
    update_data = payload.dict(exclude_unset=True)
    updated_user = user_repo.update_profile(
        current_user,
        name=update_data.get("name"),
        phone=update_data.get("phone"),
        avatar_url=update_data.get("avatar_url"),
        language=update_data.get("language"),
    )
    return UserMeResponse.from_orm(updated_user)


@router.get("/{user_id}", response_model=UserPublicProfileResponse)
def read_user_profile(
    user_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    user_repo: UserRepository = Depends(deps.get_user_repository),
) -> UserPublicProfileResponse:
    user = user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublicProfileResponse.from_orm(user)
