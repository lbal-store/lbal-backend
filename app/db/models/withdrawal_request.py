from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.models.transaction import TransactionStatus


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    destination = Column(Text, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.pending)
    idempotency_key = Column(String(128), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
