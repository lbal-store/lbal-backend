from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.notification import Notification, NotificationEvent
from app.db.models.order import Order, OrderStatus
from app.db.models.withdrawal_request import WithdrawalRequest
from app.db.repositories.notification_repository import NotificationRepository
from app.db.repositories.user_repository import UserRepository


class NotificationService:
    def __init__(
        self,
        *,
        db: Session,
        notification_repository: NotificationRepository,
        user_repository: UserRepository,
    ) -> None:
        self.db = db
        self.notification_repository = notification_repository
        self.user_repository = user_repository

    def create_notification(
        self,
        *,
        user_id: UUID,
        event: NotificationEvent,
        payload: dict[str, Any] | None = None,
    ) -> Notification:
        notification = self.notification_repository.create(user_id=user_id, event=event, payload=payload or {})
        self.user_repository.set_has_unread_notifications(user_id, True, commit=False)
        return notification

    def list_for_user(self, *, user_id: UUID, mark_as_read: bool = False, limit: int = 50) -> list[Notification]:
        notifications = list(self.notification_repository.list_for_user(user_id, limit=limit))
        if mark_as_read:
            self.notification_repository.mark_all_read(user_id)
            self.user_repository.set_has_unread_notifications(user_id, False, commit=False)
            self.db.commit()
        return notifications

    def notify_item_sold(self, order: Order) -> None:
        payload = {
            "order_id": str(order.id),
            "listing_id": str(order.listing_id),
            "buyer_id": str(order.buyer_id),
        }
        self.create_notification(user_id=order.seller_id, event=NotificationEvent.item_sold, payload=payload)

    def notify_order_transition(self, order: Order, new_status: OrderStatus) -> None:
        event = self._event_for_status(new_status)
        if not event:
            return

        payload = {
            "order_id": str(order.id),
            "listing_id": str(order.listing_id),
            "status": new_status.value,
        }
        self.create_notification(user_id=order.buyer_id, event=event, payload=payload)

    def notify_withdrawal_created(self, withdrawal: WithdrawalRequest) -> None:
        payload = {
            "withdrawal_id": str(withdrawal.id),
            "amount": str(withdrawal.amount),
            "destination": withdrawal.destination,
        }
        self.create_notification(user_id=withdrawal.user_id, event=NotificationEvent.withdrawal_created, payload=payload)

    def _event_for_status(self, status: OrderStatus) -> NotificationEvent | None:
        mapping: dict[OrderStatus, NotificationEvent] = {
            OrderStatus.confirmed: NotificationEvent.order_confirmed,
            OrderStatus.shipped: NotificationEvent.order_shipped,
            OrderStatus.delivered: NotificationEvent.order_delivered,
        }
        return mapping.get(status)
