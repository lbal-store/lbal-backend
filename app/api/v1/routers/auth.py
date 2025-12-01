from fastapi import APIRouter, Depends, Request, status

from app.api.v1 import deps
from app.api.v1.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    SignupRequest,
    SignupResponse,
    VerifyEmailRequest,
)
from app.db.models.user import User
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> SignupResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.signup(name=payload.name, email=payload.email, password=payload.password, user_agent=user_agent, ip=client_ip)


@router.post("/verify-email", response_model=LoginResponse)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> LoginResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.verify_email(email=payload.email, code=payload.code, user_agent=user_agent, ip=client_ip)


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    payload: ResendVerificationRequest,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> MessageResponse:
    return auth_service.resend_verification(email=payload.email)


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(deps.enforce_login_rate_limit)])
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> LoginResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.login(email=payload.email, password=payload.password, user_agent=user_agent, ip=client_ip)


@router.post("/google", response_model=LoginResponse)
def google_login(
    payload: GoogleAuthRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> LoginResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_service.google_login(id_token=payload.id_token, user_agent=user_agent, ip=client_ip)


@router.post("/refresh", response_model=LoginResponse)
def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> LoginResponse:
    token = deps.extract_refresh_token(request, payload.refresh_token)
    return auth_service.refresh(refresh_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest | None,
    request: Request,
    auth_service: AuthService = Depends(deps.get_auth_service),
) -> None:
    all_sessions = payload.all if payload else False
    token = deps.extract_refresh_token(request, None)
    auth_service.logout(refresh_token=token, all_sessions=all_sessions)


@router.post("/logout-all", status_code=status.HTTP_200_OK)
def logout_all(
    auth_service: AuthService = Depends(deps.get_auth_service),
    current_user: User = Depends(deps.get_current_user),
) -> dict[str, str]:
    auth_service.logout_all(user_id=current_user.id)
    return {"detail": "All sessions revoked"}
