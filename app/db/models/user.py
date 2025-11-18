import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class KycStatus(str, enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(50))
    avatar_url = Column(String(512))
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    language = Column(String(10), default="fr")
    kyc_status = Column(Enum(KycStatus), nullable=False, default=KycStatus.unverified)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
