from __future__ import annotations

from uuid import UUID

from fastapi import status

from app.api.v1.schemas.listings import (
    ListingCreate,
    ListingFilterParams,
    ListingImageCreate,
    ListingSortOption,
    ListingUpdate,
)
from app.core.errors import ApplicationError, ErrorCode
from app.db.models.listing import Listing
from app.db.models.listing_image import ListingImage
from app.db.repositories.category_repository import CategoryRepository
from app.db.repositories.listing_repository import ListingRepository
from app.db.repositories.listing_image_repository import ListingImageRepository


MAX_LISTING_IMAGES = 10
MAX_PAGE_SIZE = 50


class ListingService:
    def __init__(
        self,
        listing_repository: ListingRepository,
        listing_image_repository: ListingImageRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self.listing_repository = listing_repository
        self.listing_image_repository = listing_image_repository
        self.category_repository = category_repository

    def create_listing(self, user_id: UUID, payload: ListingCreate) -> Listing:
        self._validate_category(payload.category_id)
        data = payload.dict()
        return self.listing_repository.create_listing(user_id, data)

    def bulk_create_listings(self, user_id: UUID, payloads: list[ListingCreate]) -> list[Listing]:
        listings: list[Listing] = []
        for payload in payloads:
            listings.append(self.create_listing(user_id, payload))
        return listings

    def update_listing(self, user_id: UUID, listing_id: UUID, payload: ListingUpdate) -> Listing:
        listing = self._get_listing_or_404(listing_id)
        self._ensure_listing_owner(listing, user_id)

        data = payload.dict(exclude_unset=True)
        if "category_id" in data:
            self._validate_category(data["category_id"])

        if not data:
            return listing

        return self.listing_repository.update_listing(listing, data)

    def delete_listing(self, user_id: UUID, listing_id: UUID) -> None:
        listing = self._get_listing_or_404(listing_id)
        self._ensure_listing_owner(listing, user_id)
        self.listing_repository.delete_listing(listing)

    def get_user_listings(self, user_id: UUID) -> list[Listing]:
        return list(self.listing_repository.get_listings_by_user(user_id))

    def get_listing(self, listing_id: UUID) -> Listing:
        return self._get_listing_or_404(listing_id)

    def search_public_listings(
        self,
        filters: ListingFilterParams,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Listing], int, int, int]:
        category_id = self._resolve_category_filter(filters.category_id)
        self._validate_category(category_id)

        page_size = min(page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        listings, total = self.listing_repository.search_listings(
            category_id=category_id,
            city=filters.city,
            min_price=filters.min_price,
            max_price=filters.max_price,
            condition=filters.condition,
            sort_by=filters.sort_by.value if isinstance(filters.sort_by, ListingSortOption) else filters.sort_by,
            limit=page_size,
            offset=offset,
        )

        return listings, total, page, page_size

    def add_listing_image(self, user_id: UUID, listing_id: UUID, payload: ListingImageCreate) -> ListingImage:
        listing = self._get_listing_or_404(listing_id)
        self._ensure_listing_owner(listing, user_id)

        existing_images = list(self.listing_image_repository.get_images_for_listing(listing_id))
        if len(existing_images) >= MAX_LISTING_IMAGES:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"A listing can have at most {MAX_LISTING_IMAGES} images.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        position = payload.position if payload.position is not None else len(existing_images)
        if position < 0 or position > len(existing_images):
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid image position.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        self.listing_image_repository.shift_positions_for_listing(listing_id, starting_from=position)

        return self.listing_image_repository.add_image(listing_id, str(payload.url), position)

    def remove_listing_image(self, user_id: UUID, image_id: UUID) -> None:
        image = self.listing_image_repository.get_image_by_id(image_id)
        if not image:
            raise ApplicationError(
                code="NOT_FOUND",
                message="Listing image not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        listing = self._get_listing_or_404(image.listing_id)
        self._ensure_listing_owner(listing, user_id)
        self.listing_image_repository.remove_image(image)

    def _get_listing_or_404(self, listing_id: UUID) -> Listing:
        listing = self.listing_repository.get_listing_by_id(listing_id)
        if not listing:
            raise ApplicationError(
                code="NOT_FOUND",
                message="Listing not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return listing

    @staticmethod
    def _ensure_listing_owner(listing: Listing, user_id: UUID) -> None:
        if listing.user_id != user_id:
            raise ApplicationError(
                code=ErrorCode.ACCESS_DENIED,
                message="You are not allowed to modify this listing.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def _validate_category(self, category_id: UUID | None) -> None:
        if category_id and not self.category_repository.exists(category_id):
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Category does not exist.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def _resolve_category_filter(self, category_identifier: UUID | str | None) -> UUID | None:
        if not category_identifier:
            return None

        if isinstance(category_identifier, UUID):
            return category_identifier

        identifier = str(category_identifier).strip()
        if not identifier:
            return None

        try:
            return UUID(identifier)
        except ValueError:
            category = self.category_repository.get_by_name(identifier)
            if not category:
                raise ApplicationError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Category does not exist.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            return category.id
