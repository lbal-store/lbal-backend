from app.core.security import create_access_token, verify_password


class AuthService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def authenticate(self, email: str, password: str) -> str | None:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return create_access_token(subject=str(user.id))
