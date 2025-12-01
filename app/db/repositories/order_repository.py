from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.order import Order


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **data: object) -> Order:
        order = Order(**data)
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def get_by_id(self, order_id: UUID) -> Order | None:
        return self.db.get(Order, order_id)

    def get_by_idempotency_key(self, key: str) -> Order | None:
        if not key:
            return None
        return self.db.query(Order).filter(Order.idempotency_key == key).one_or_none()

    def get_by_buyer(self, buyer_id: UUID) -> Sequence[Order]:
        return (
            self.db.query(Order)
            .filter(Order.buyer_id == buyer_id)
            .order_by(Order.created_at.desc())
            .all()
        )

    def get_by_seller(self, seller_id: UUID) -> Sequence[Order]:
        return (
            self.db.query(Order)
            .filter(Order.seller_id == seller_id)
            .order_by(Order.created_at.desc())
            .all()
        )

    def save(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order
