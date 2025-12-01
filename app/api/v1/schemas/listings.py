from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, condecimal

from app.db.models.listing import ListingCondition, ListingStatus


DecimalMoney = condecimal(gt=0, max_digits=12, decimal_places=2)


class ListingBase(BaseModel):
    title: str = Field(..., max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    category_id: Optional[uuid.UUID] = Field(default=None)
    brand: Optional[str] = Field(default=None, max_length=60)
    size: Optional[str] = Field(default=None, max_length=60)
    condition: ListingCondition
    price: DecimalMoney
    city: str = Field(..., max_length=60)


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    category_id: Optional[uuid.UUID] = None
    brand: Optional[str] = Field(default=None, max_length=60)
    size: Optional[str] = Field(default=None, max_length=60)
    condition: Optional[ListingCondition] = None
    price: Optional[DecimalMoney] = None
    city: Optional[str] = Field(default=None, max_length=60)


class ListingResponse(ListingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: ListingStatus
    created_at: datetime
    updated_at: datetime
    images: list["ListingImageResponse"] = Field(default_factory=list)


class ListingSortOption(str, Enum):
    price = "price"
    newest = "newest"
    oldest = "oldest"


class ListingFilterParams(BaseModel):
    category_id: Optional[str] = None
    city: Optional[str] = None
    condition: Optional[ListingCondition] = None
    min_price: Optional[Decimal] = Field(default=None, gt=0)
    max_price: Optional[Decimal] = Field(default=None, gt=0)
    sort_by: ListingSortOption = Field(default=ListingSortOption.newest)


class ListingImageCreate(BaseModel):
    url: HttpUrl
    position: Optional[int] = Field(default=None, ge=0)


class ListingImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    url: HttpUrl
    position: int
    created_at: datetime


class CreateListingImageRequest(BaseModel):
    url: HttpUrl
    position: Optional[int] = Field(default=None, ge=0)


class BulkListingCreateRequest(BaseModel):
    listings: list[ListingCreate] = Field(..., min_length=1, description="Listings to create.")


class ListingListResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    page_size: int
