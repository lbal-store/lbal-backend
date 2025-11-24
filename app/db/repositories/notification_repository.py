from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db.models.notification import Notification, NotificationEvent


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        event: NotificationEvent,
        payload: dict[str, object] | None = None,
    ) -> Notification:
        notification = Notification(user_id=user_id, event=event, payload=payload or {})
        self.db.add(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def list_for_user(self, user_id: UUID, limit: int = 50) -> Sequence[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_all_read(self, user_id: UUID) -> int:
        updated = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({"is_read": True, "read_at": func.now()}, synchronize_session=False)
        )
        self.db.flush()
        return int(updated)
