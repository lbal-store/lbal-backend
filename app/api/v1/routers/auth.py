from fastapi import APIRouter, Depends, Request, status

from app.api.v1 import deps
from app.api.v1.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPair
from app.db.models.user import User
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair, dependencies=[Depends(deps.enforce_login_rate_limit)])
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> TokenPair:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.login(email=payload.email, password=payload.password, user_agent=user_agent, ip=client_ip)


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> TokenPair:
    return auth_service.refresh(refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: LogoutRequest,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> dict[str, str]:
    auth_service.logout(refresh_token=payload.refresh_token)
    return {"detail": "Logged out"}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
def logout_all(
    auth_service: AuthService = Depends(deps.get_auth_service),
    current_user: User = Depends(deps.get_current_user),
) -> dict[str, str]:
    auth_service.logout_all(user_id=current_user.id)
    return {"detail": "All sessions revoked"}
