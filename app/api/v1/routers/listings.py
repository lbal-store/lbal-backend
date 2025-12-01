from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status

from app.api.v1 import deps
from app.api.v1.schemas.listings import (
    ListingCreate,
    ListingFilterParams,
    BulkListingCreateRequest,
    CreateListingImageRequest,
    ListingImageCreate,
    ListingImageResponse,
    ListingListResponse,
    ListingResponse,
    ListingUpdate,
)
from app.core.errors import ApplicationError, ErrorCode
from app.db.models.user import User, UserRole
from app.services.listing_service import ListingService
from app.services.s3_service import S3Service


router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=ListingListResponse)
def search_listings(
    filters: ListingFilterParams = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> ListingListResponse:
    listings, total, page_value, resolved_page_size = listing_service.search_public_listings(
        filters,
        page=page,
        page_size=page_size,
    )
    return ListingListResponse(
        items=[ListingResponse.from_orm(listing) for listing in listings],
        total=total,
        page=page_value,
        page_size=resolved_page_size,
    )


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing(
    payload: ListingCreate,
    current_user: User = Depends(deps.enforce_listing_create_rate_limit),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> ListingResponse:
    listing = listing_service.create_listing(current_user.id, payload)
    return ListingResponse.from_orm(listing)


@router.post(
    "/bulk",
    response_model=list[ListingResponse],
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_listings(
    payload: BulkListingCreateRequest,
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> list[ListingResponse]:
    if current_user.role != UserRole.admin:
        raise ApplicationError(
            code=ErrorCode.ACCESS_DENIED,
            message="Only administrators can bulk create listings.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    listings = listing_service.bulk_create_listings(current_user.id, payload.listings)
    return [ListingResponse.from_orm(listing) for listing in listings]


@router.get("/me", response_model=list[ListingResponse])
def list_my_listings(
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> list[ListingResponse]:
    listings = listing_service.get_user_listings(current_user.id)
    return [ListingResponse.from_orm(listing) for listing in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(
    listing_id: UUID,
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> ListingResponse:
    listing = listing_service.get_listing(listing_id)
    return ListingResponse.from_orm(listing)


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: UUID,
    payload: ListingUpdate,
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> ListingResponse:
    listing = listing_service.update_listing(current_user.id, listing_id, payload)
    return ListingResponse.from_orm(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> None:
    listing_service.delete_listing(current_user.id, listing_id)


@router.post(
    "/{listing_id}/images",
    response_model=ListingImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_listing_image(
    listing_id: UUID,
    payload: CreateListingImageRequest,
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> ListingImageResponse:
    image_payload = ListingImageCreate(url=payload.url, position=payload.position)
    image = listing_service.add_listing_image(current_user.id, listing_id, image_payload)
    return ListingImageResponse.from_orm(image)


@router.delete("/images/{image_id}")
def remove_listing_image(
    image_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
) -> dict[str, str]:
    listing_service.remove_listing_image(current_user.id, image_id)
    return {"detail": "deleted"}


@router.post("/{listing_id}/images/presign")
def presign_listing_image(
    listing_id: UUID,
    content_type: str = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_user),
    listing_service: ListingService = Depends(deps.get_listing_service),
    s3_service: S3Service = Depends(deps.get_s3_service),
) -> dict[str, str]:
    listing = listing_service.get_listing(listing_id)
    if listing.user_id != current_user.id:
        raise ApplicationError(
            code=ErrorCode.ACCESS_DENIED,
            message="You are not allowed to upload images for this listing.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    upload_url, final_url = s3_service.generate_presigned_upload(content_type=content_type)
    return {"upload_url": upload_url, "final_url": final_url}
