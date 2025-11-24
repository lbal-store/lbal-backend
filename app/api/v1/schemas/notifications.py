from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.models.notification import NotificationEvent


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event: NotificationEvent
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None
