from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.api.v1.schemas.orders import OrderCreateRequest
from app.core.errors import ApplicationError, ErrorCode
from app.db.models.address import Address
from app.db.models.listing import Listing, ListingStatus
from app.db.models.order import Order, OrderStatus
from app.db.models.user import User, UserRole
from app.db.repositories.address_repository import AddressRepository
from app.db.repositories.listing_repository import ListingRepository
from app.db.repositories.order_repository import OrderRepository
from app.services.wallet_service import WalletService
from app.services.notification_service import NotificationService


ZERO = Decimal("0")


class OrderService:
    def __init__(
        self,
        db: Session,
        order_repository: OrderRepository,
        listing_repository: ListingRepository,
        address_repository: AddressRepository,
        wallet_service: WalletService,
        notification_service: NotificationService,
    ) -> None:
        self.db = db
        self.order_repository = order_repository
        self.listing_repository = listing_repository
        self.address_repository = address_repository
        self.wallet_service = wallet_service
        self.notification_service = notification_service

    def create_order(self, buyer_id: UUID, payload: OrderCreateRequest) -> Order:
        existing = self.order_repository.get_by_idempotency_key(payload.idempotency_key)
        if existing:
            if existing.buyer_id != buyer_id:
                raise ApplicationError(
                    code=ErrorCode.ACCESS_DENIED,
                    message="This order belongs to another buyer.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            return existing

        address = self.address_repository.get_by_id_and_user(payload.shipping_address_id, buyer_id)
        if not address:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Shipping address not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        listing = self.listing_repository.check_availability(payload.listing_id, for_update=True)
        if not listing:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Listing not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        self._ensure_listing_is_available(listing, buyer_id)

        snapshot = self._build_address_snapshot(address)

        try:
            self.listing_repository.lock_listing(listing)
            order = self.order_repository.create(
                listing_id=listing.id,
                buyer_id=buyer_id,
                seller_id=listing.user_id,
                shipping_address_id=address.id,
                shipping_address_snapshot=snapshot,
                price_amount=listing.price,
                buyer_fee=ZERO,
                idempotency_key=payload.idempotency_key,
            )
            self.wallet_service.hold_funds(user_id=buyer_id, order_id=order.id, amount=listing.price)
            self.notification_service.notify_item_sold(order)
            self.db.commit()
        except Exception:  # pragma: no cover - ensures atomic insert
            self.db.rollback()
            raise

        return order

    def get_buyer_orders(self, buyer_id: UUID) -> list[Order]:
        return list(self.order_repository.get_by_buyer(buyer_id))

    def get_seller_orders(self, seller_id: UUID) -> list[Order]:
        return list(self.order_repository.get_by_seller(seller_id))

    def get_order(self, order_id: UUID, current_user: User) -> Order:
        order = self._get_order_or_404(order_id)
        self._ensure_order_access(order, current_user)
        return order

    def update_status(self, order_id: UUID, *, new_status: OrderStatus, actor: User) -> Order:
        order = self._get_order_or_404(order_id)
        self._ensure_order_access(order, actor)

        if order.status == new_status:
            return order

        if not self._is_transition_allowed(order, new_status, actor):
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid status transition.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        prev_status = order.status
        order.status = new_status
        self._sync_listing_state(order, prev_status, new_status)
        self._apply_wallet_side_effects(order, prev_status, new_status)
        self.notification_service.notify_order_transition(order, new_status)

        try:
            self.order_repository.save(order)
            self.db.commit()
        except Exception:  # pragma: no cover
            self.db.rollback()
            raise

        return order

    def _ensure_listing_is_available(self, listing: Listing, buyer_id: UUID) -> None:
        if listing.status != ListingStatus.approved:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Listing is not available for purchase.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if listing.is_locked:
            raise ApplicationError(
                code=ErrorCode.CONFLICT,
                message="Listing is locked by another order.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if listing.sold_at is not None:
            raise ApplicationError(
                code=ErrorCode.CONFLICT,
                message="Listing has already been sold.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if listing.user_id == buyer_id:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="You cannot purchase your own listing.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def _build_address_snapshot(self, address: Address) -> dict[str, str | None]:
        return {
            "line1": address.line1,
            "line2": address.line2,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
            "country": address.country,
        }

    def _get_order_or_404(self, order_id: UUID) -> Order:
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Order not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return order

    def _ensure_order_access(self, order: Order, actor: User) -> None:
        if actor.role == UserRole.admin:
            return
        if order.buyer_id != actor.id and order.seller_id != actor.id:
            raise ApplicationError(
                code=ErrorCode.ACCESS_DENIED,
                message="You do not have access to this order.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def _is_transition_allowed(self, order: Order, new_status: OrderStatus, actor: User) -> bool:
        current = order.status

        if new_status == OrderStatus.canceled:
            if actor.role == UserRole.admin:
                return True
            return actor.id == order.seller_id and current == OrderStatus.pending

        if actor.id == order.seller_id:
            if current == OrderStatus.pending and new_status == OrderStatus.confirmed:
                return True
            if current == OrderStatus.confirmed and new_status == OrderStatus.shipped:
                return True

        if actor.role == UserRole.admin and current == OrderStatus.shipped and new_status == OrderStatus.delivered:
            return True

        if actor.id == order.buyer_id and current == OrderStatus.delivered and new_status == OrderStatus.completed:
            return True

        return False

    def _sync_listing_state(self, order: Order, previous: OrderStatus, new_status: OrderStatus) -> None:
        listing = order.listing
        if not listing:
            return

        if new_status == OrderStatus.canceled:
            self.listing_repository.release_listing(listing, new_status=ListingStatus.approved)
            listing.sold_at = None
        elif previous != OrderStatus.completed and new_status == OrderStatus.completed:
            listing.sold_at = datetime.now(timezone.utc)

    def _apply_wallet_side_effects(self, order: Order, previous: OrderStatus, new_status: OrderStatus) -> None:
        amount = order.price_amount
        if new_status == OrderStatus.canceled and previous != OrderStatus.canceled:
            self.wallet_service.release_hold(
                user_id=order.buyer_id,
                order_id=order.id,
                amount=amount,
                refund_to_balance=True,
            )
            return

        if new_status == OrderStatus.completed and previous != OrderStatus.completed:
            self.wallet_service.release_hold(
                user_id=order.buyer_id,
                order_id=order.id,
                amount=amount,
                refund_to_balance=False,
            )
            self.wallet_service.credit_user(
                user_id=order.seller_id,
                amount=amount,
                order_id=order.id,
                description="Order payout",
            )
