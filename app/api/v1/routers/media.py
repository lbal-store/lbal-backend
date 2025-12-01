from fastapi import APIRouter, Depends

from app.api.v1 import deps
from app.db.models.user import User


router = APIRouter(prefix="/media", tags=["media"])


@router.get("/ping")
async def ping_media() -> dict[str, str]:
    return {"router": "media", "status": "ok"}


@router.post("/presign")
def create_presigned_url(current_user: User = Depends(deps.enforce_media_presign_rate_limit)) -> dict[str, str]:
    return {
        "message": "Presign endpoint placeholder",
        "user_id": str(current_user.id),
    }
