from fastapi import APIRouter, Depends, status

from app.api.v1 import deps
from app.api.v1.schemas.wallet import WalletResponse, WithdrawalRequestCreate, WithdrawalRequestResponse
from app.db.models.user import User
from app.services.wallet_service import WalletService


router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/ping")
async def ping_wallet() -> dict[str, str]:
    return {"router": "wallet", "status": "ok"}


@router.get("/me", response_model=WalletResponse)
def get_my_wallet(
    current_user: User = Depends(deps.get_current_user),
    wallet_service: WalletService = Depends(deps.get_wallet_service),
) -> WalletResponse:
    wallet = wallet_service.get_wallet(current_user.id)
    return WalletResponse.model_validate(wallet)


@router.post("/withdraw", response_model=WithdrawalRequestResponse, status_code=status.HTTP_201_CREATED)
def request_withdrawal(
    payload: WithdrawalRequestCreate,
    current_user: User = Depends(deps.get_current_user),
    wallet_service: WalletService = Depends(deps.get_wallet_service),
) -> WithdrawalRequestResponse:
    withdrawal = wallet_service.request_withdrawal(
        user_id=current_user.id,
        amount=payload.amount,
        destination=payload.destination,
        idempotency_key=payload.idempotency_key,
    )
    return WithdrawalRequestResponse.model_validate(withdrawal)
