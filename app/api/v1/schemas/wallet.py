from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.transaction import TransactionStatus


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    balance: Decimal
    updated_at: datetime | None = None


class WithdrawalRequestCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    destination: str = Field(..., min_length=3, max_length=255)
    idempotency_key: str | None = Field(default=None, max_length=128)


class WithdrawalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    destination: str
    status: TransactionStatus
    created_at: datetime
