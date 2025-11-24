from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class NotificationEvent(str, enum.Enum):
    order_confirmed = "order_confirmed"
    order_shipped = "order_shipped"
    order_delivered = "order_delivered"
    item_sold = "item_sold"
    withdrawal_created = "withdrawal_created"
    buyer_question = "buyer_question"
    dispute_opened = "dispute_opened"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event = Column(Enum(NotificationEvent, name="notificationevent"), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="notifications")
