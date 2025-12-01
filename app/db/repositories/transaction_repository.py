from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.transaction import Transaction, TransactionStatus, TransactionType


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        amount,
        type: TransactionType,
        status: TransactionStatus,
        order_id: UUID | None = None,
        destination: str | None = None,
        description: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            status=status,
            order_id=order_id,
            destination=destination,
            description=description,
        )
        self.db.add(transaction)
        self.db.flush()
        self.db.refresh(transaction)
        return transaction

    def has_transaction(
        self,
        *,
        user_id: UUID,
        order_id: UUID | None,
        type: TransactionType,
    ) -> bool:
        query = self.db.query(Transaction.id).filter(Transaction.user_id == user_id, Transaction.type == type)
        if order_id:
            query = query.filter(Transaction.order_id == order_id)
        else:
            query = query.filter(Transaction.order_id.is_(None))
        return query.first() is not None
