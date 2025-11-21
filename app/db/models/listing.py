from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ListingStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    sold = "sold"
    archived = "archived"


class ListingCondition(str, enum.Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"
    poor = "poor"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(2000))
    category_id = Column("category", UUID(as_uuid=True), ForeignKey("categories.id"))
    brand = Column(String(60))
    size = Column(String(60))
    condition = Column(Enum(ListingCondition), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    city = Column(String(60), nullable=False)
    status = Column(Enum(ListingStatus), nullable=False, default=ListingStatus.pending)
    is_locked = Column(Boolean, nullable=False, default=False)
    sold_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    images = relationship(
        "ListingImage",
        back_populates="listing",
        order_by="ListingImage.position",
        cascade="all, delete-orphan",
    )
