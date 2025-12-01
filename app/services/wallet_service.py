from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError, ErrorCode
from app.db.models.wallet import Wallet
from app.db.models.withdrawal_request import WithdrawalRequest
from app.db.models.transaction import TransactionStatus, TransactionType
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.repositories.wallet_repository import WalletRepository
from app.db.repositories.withdrawal_request_repository import WithdrawalRequestRepository
from app.services.notification_service import NotificationService


ZERO = Decimal("0")


class WalletService:
    def __init__(
        self,
        *,
        db: Session,
        wallet_repository: WalletRepository,
        transaction_repository: TransactionRepository,
        withdrawal_repository: WithdrawalRequestRepository,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.db = db
        self.wallet_repository = wallet_repository
        self.transaction_repository = transaction_repository
        self.withdrawal_repository = withdrawal_repository
        self.notification_service = notification_service

    def get_wallet(self, user_id: UUID) -> Wallet:
        wallet = self.wallet_repository.get_by_user_id(user_id)
        if not wallet:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Wallet not found.",
                status_code=404,
            )
        return wallet

    def hold_funds(self, *, user_id: UUID, order_id: UUID, amount: Decimal) -> None:
        if self.transaction_repository.has_transaction(user_id=user_id, order_id=order_id, type=TransactionType.hold):
            return
        wallet = self._lock_wallet(user_id)
        self._assert_sufficient_balance(wallet, amount)
        wallet.balance -= amount
        self.wallet_repository.save(wallet)
        self.transaction_repository.create(
            user_id=user_id,
            amount=amount,
            order_id=order_id,
            type=TransactionType.hold,
            status=TransactionStatus.succeeded,
            description="Hold funds for order",
        )

    def release_hold(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount: Decimal,
        refund_to_balance: bool,
    ) -> None:
        if self.transaction_repository.has_transaction(user_id=user_id, order_id=order_id, type=TransactionType.release):
            return
        wallet = self._lock_wallet(user_id)
        if refund_to_balance:
            wallet.balance += amount
            self.wallet_repository.save(wallet)
        self.transaction_repository.create(
            user_id=user_id,
            amount=amount,
            order_id=order_id,
            type=TransactionType.release,
            status=TransactionStatus.succeeded,
            description="Release funds",
        )

    def credit_user(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        order_id: UUID | None = None,
        description: str | None = None,
    ) -> None:
        if order_id and self.transaction_repository.has_transaction(
            user_id=user_id,
            order_id=order_id,
            type=TransactionType.credit,
        ):
            return
        wallet = self._lock_wallet(user_id)
        wallet.balance += amount
        self.wallet_repository.save(wallet)
        self.transaction_repository.create(
            user_id=user_id,
            amount=amount,
            order_id=order_id,
            type=TransactionType.credit,
            status=TransactionStatus.succeeded,
            description=description or "Wallet credit",
        )

    def debit_user(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        description: str | None = None,
        order_id: UUID | None = None,
    ) -> None:
        wallet = self._lock_wallet(user_id)
        self._assert_sufficient_balance(wallet, amount)
        wallet.balance -= amount
        self.wallet_repository.save(wallet)
        self.transaction_repository.create(
            user_id=user_id,
            amount=amount,
            order_id=order_id,
            type=TransactionType.debit,
            status=TransactionStatus.succeeded,
            description=description or "Wallet debit",
        )

    def request_withdrawal(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        destination: str,
        idempotency_key: str | None = None,
    ) -> WithdrawalRequest:
        if idempotency_key:
            existing = self.withdrawal_repository.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing
        wallet = self._lock_wallet(user_id)
        self._assert_sufficient_balance(wallet, amount)

        try:
            withdrawal = self.withdrawal_repository.create(
                user_id=user_id,
                amount=amount,
                destination=destination,
                status=TransactionStatus.succeeded,
                idempotency_key=idempotency_key,
            )

            wallet.balance -= amount
            self.wallet_repository.save(wallet)
            self.transaction_repository.create(
                user_id=user_id,
                amount=amount,
                type=TransactionType.debit,
                status=TransactionStatus.succeeded,
                destination=destination,
                description="Withdrawal request",
            )
            if self.notification_service:
                self.notification_service.notify_withdrawal_created(withdrawal)
            self.db.commit()
        except Exception:  # pragma: no cover - ensures atomic insert
            self.db.rollback()
            raise

        return withdrawal

    def _lock_wallet(self, user_id: UUID) -> Wallet:
        wallet = self.wallet_repository.get_for_update(user_id)
        if not wallet:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Wallet not found.",
                status_code=404,
            )
        return wallet

    def _assert_sufficient_balance(self, wallet: Wallet, amount: Decimal) -> None:
        if amount <= ZERO:
            raise ApplicationError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Amount must be greater than zero.",
                status_code=400,
            )
        if wallet.balance < amount:
            raise ApplicationError(
                code=ErrorCode.INSUFFICIENT_FUNDS,
                message="Insufficient wallet balance.",
                status_code=400,
            )
