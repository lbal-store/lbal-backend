from fastapi import APIRouter, Depends

from app.api.v1 import deps
from app.db.models.user import User


router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/ping")
async def ping_listings() -> dict[str, str]:
    return {"router": "listings", "status": "ok"}


@router.post("")
def create_listing_stub(current_user: User = Depends(deps.enforce_listing_create_rate_limit)) -> dict[str, str]:
    return {"message": "Listing creation placeholder", "user_id": str(current_user.id)}
