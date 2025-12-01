from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.order import OrderStatus


class ShippingAddressSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str | None = None
    country: str


class OrderCreateRequest(BaseModel):
    listing_id: uuid.UUID
    shipping_address_id: uuid.UUID
    idempotency_key: str = Field(..., max_length=128)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    price_amount: Decimal
    buyer_fee: Decimal
    status: OrderStatus
    shipping_address_snapshot: ShippingAddressSnapshot
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus
