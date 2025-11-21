from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.listing import Listing
from app.db.models.listing_image import ListingImage


class ListingImageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_image(self, listing_id: UUID, url: str, position: int) -> ListingImage:
        image = ListingImage(listing_id=listing_id, url=url, position=position)
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def remove_image(self, image: ListingImage) -> None:
        self.db.delete(image)
        self.db.commit()

    def get_images_for_listing(self, listing_id: UUID) -> Sequence[ListingImage]:
        return (
            self.db.query(ListingImage)
            .filter(ListingImage.listing_id == listing_id)
            .order_by(ListingImage.position.asc(), ListingImage.created_at.asc())
            .all()
        )

    def get_image_by_id(self, image_id: UUID) -> ListingImage | None:
        return self.db.get(ListingImage, image_id)

    def get_listing_for_image(self, image_id: UUID) -> Listing | None:
        image = self.get_image_by_id(image_id)
        if not image:
            return None
        return self.db.get(Listing, image.listing_id)

    def shift_positions_for_listing(self, listing_id: UUID, starting_from: int = 0) -> None:
        (
            self.db.query(ListingImage)
            .filter(ListingImage.listing_id == listing_id, ListingImage.position >= starting_from)
            .update({ListingImage.position: ListingImage.position + 1})
        )
        self.db.commit()

    # Convenience aliases for compatibility with different naming expectations
    def create(self, listing_id: UUID, url: str, position: int) -> ListingImage:
        return self.add_image(listing_id, url, position)

    def get(self, image_id: UUID) -> ListingImage | None:
        return self.get_image_by_id(image_id)

    def delete(self, image_id: UUID) -> None:
        image = self.get_image_by_id(image_id)
        if image:
            self.remove_image(image)

    def list_for_listing(self, listing_id: UUID) -> Sequence[ListingImage]:
        return self.get_images_for_listing(listing_id)
