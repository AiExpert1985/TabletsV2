"""SQLAlchemy ORM models for authentication."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, String, DateTime, ForeignKey, Index, TypeDecorator, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enum."""
    SYSTEM_ADMIN = "system_admin"
    COMPANY_ADMIN = "company_admin"
    USER = "user"


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36) for SQLite.
    Stores UUID as string with hyphens for consistency.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite: store as string with hyphens
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        # Convert string back to UUID
        return uuid.UUID(value)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Multi-tenancy fields
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,  # NULL for system_admin
        index=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=50),
        default=UserRole.USER,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="users",
        foreign_keys=[company_id]
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.phone_number}>"


class RefreshToken(Base):
    """Refresh token model - stores hashed tokens."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    device_info: Mapped[dict | None] = mapped_column(String, nullable=True)  # JSONB for future

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken {self.token_id[:8]}...>"


# Additional indexes for performance
Index('idx_refresh_tokens_user_expires', RefreshToken.user_id, RefreshToken.expires_at)
