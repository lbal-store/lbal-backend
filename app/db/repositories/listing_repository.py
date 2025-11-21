from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.listing import Listing, ListingCondition, ListingStatus


class ListingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_listing(self, user_id: UUID, data: dict[str, Any]) -> Listing:
        listing = Listing(user_id=user_id, status=ListingStatus.pending, **data)
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def get_listing_by_id(self, listing_id: UUID) -> Listing | None:
        return self.db.get(Listing, listing_id)

    def update_listing(self, listing: Listing, data: dict[str, Any]) -> Listing:
        for key, value in data.items():
            setattr(listing, key, value)
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def delete_listing(self, listing: Listing) -> None:
        self.db.delete(listing)
        self.db.commit()

    def get_listings_by_user(self, user_id: UUID) -> Sequence[Listing]:
        return (
            self.db.query(Listing)
            .filter(Listing.user_id == user_id)
            .order_by(Listing.created_at.desc())
            .all()
        )

    def search_listings(
        self,
        *,
        category_id: UUID | None = None,
        city: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        condition: ListingCondition | None = None,
        sort_by: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Listing], int]:
        query = (
            self.db.query(Listing)
            .filter(
                Listing.status == ListingStatus.approved,
                Listing.is_locked.is_(False),
                Listing.sold_at.is_(None),
            )
        )

        if category_id:
            query = query.filter(Listing.category_id == category_id)
        if city:
            query = query.filter(Listing.city == city)
        if min_price is not None:
            query = query.filter(Listing.price >= min_price)
        if max_price is not None:
            query = query.filter(Listing.price <= max_price)
        if condition:
            query = query.filter(Listing.condition == condition)

        if sort_by == "price":
            query = query.order_by(Listing.price.asc(), Listing.created_at.desc())
        elif sort_by == "oldest":
            query = query.order_by(Listing.created_at.asc())
        else:
            query = query.order_by(Listing.created_at.desc())

        total = query.count()
        listings = query.offset(offset).limit(limit).all()
        return listings, total
