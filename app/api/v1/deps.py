from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApplicationError, ErrorCode
from app.core.rate_limit import listing_create_rate_limiter, login_rate_limiter, media_presign_rate_limiter
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.models.user import User
from app.db.session import SessionLocal
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.address_repository import AddressRepository
from app.db.repositories.listing_repository import ListingRepository
from app.db.repositories.listing_image_repository import ListingImageRepository
from app.db.repositories.category_repository import CategoryRepository
from app.services.address_service import AddressService
from app.services.auth_service import AuthService
from app.services.listing_service import ListingService
from app.services.s3_service import S3Service
from app.utils.redis_client import get_redis_client


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    redis_client = get_redis_client()
    return AuthService(db, redis_client)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_address_repository(db: Session = Depends(get_db)) -> AddressRepository:
    return AddressRepository(db)


def get_listing_repository(db: Session = Depends(get_db)) -> ListingRepository:
    return ListingRepository(db)


def get_listing_image_repository(db: Session = Depends(get_db)) -> ListingImageRepository:
    return ListingImageRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_address_service(
    db: Session = Depends(get_db),
    address_repo: AddressRepository = Depends(get_address_repository),
) -> AddressService:
    return AddressService(db=db, address_repo=address_repo)


def get_listing_service(
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_image_repo: ListingImageRepository = Depends(get_listing_image_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> ListingService:
    return ListingService(
        listing_repository=listing_repo,
        listing_image_repository=listing_image_repo,
        category_repository=category_repo,
    )


def get_s3_service() -> S3Service:
    settings = get_settings()
    return S3Service(settings)


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    try:
        user_id = UUID(payload.sub)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier") from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")

    return user


def enforce_login_rate_limit(request: Request) -> None:
    identifier = request.client.host if request.client else "unknown"
    if not login_rate_limiter.allow(identifier):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Too many login attempts. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


def enforce_media_presign_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    if not media_presign_rate_limiter.allow(str(current_user.id)):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Upload limit reached. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return current_user


def enforce_listing_create_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    if not listing_create_rate_limiter.allow(str(current_user.id)):
        raise ApplicationError(
            code=ErrorCode.RATE_LIMITED,
            message="Listing creation limit reached. Try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return current_user


def extract_refresh_token(request: Request, provided_token: str | None) -> str:
    if provided_token:
        return provided_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            return token
    raise ApplicationError(
        code=ErrorCode.VALIDATION_ERROR,
        message="Refresh token is required.",
        status_code=status.HTTP_400_BAD_REQUEST,
    )
