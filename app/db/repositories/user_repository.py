from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_google_id(self, google_user_id: str) -> User | None:
        return self.db.query(User).filter(User.google_user_id == google_user_id).first()

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str | None,
        provider: str = "password",
        google_user_id: str | None = None,
        avatar_url: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            provider=provider,
            google_user_id=google_user_id,
            avatar_url=avatar_url,
            is_active=is_active,
            has_unread_notifications=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(
        self,
        user: User,
        *,
        name: str | None = None,
        phone: str | None = None,
        avatar_url: str | None = None,
        language: str | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if phone is not None:
            user.phone = phone
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if language is not None:
            user.language = language

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_active(self, user: User, *, is_active: bool) -> User:
        user.is_active = is_active
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_has_unread_notifications(self, user_id: UUID, value: bool, *, commit: bool) -> None:
        user = self.db.get(User, user_id)
        if not user:
            return
        user.has_unread_notifications = value
        self.db.add(user)
        if commit:
            self.db.commit()
            self.db.refresh(user)
        else:
            self.db.flush()
