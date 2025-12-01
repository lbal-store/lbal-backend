from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1 import deps
from app.api.v1.schemas.notifications import NotificationResponse
from app.db.models.user import User
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me", response_model=list[NotificationResponse])
def list_my_notifications(
    mark_as_read: bool = Query(False, description="Set to true to mark all notifications as read."),
    current_user: User = Depends(deps.get_current_user),
    notification_service: NotificationService = Depends(deps.get_notification_service),
) -> list[NotificationResponse]:
    notifications = notification_service.list_for_user(user_id=current_user.id, mark_as_read=mark_as_read)
    return [NotificationResponse.model_validate(notification) for notification in notifications]
