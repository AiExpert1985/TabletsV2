"""Repository layer for auth feature - abstracts database operations."""
import uuid
from datetime import datetime, timezone
from typing import Protocol
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.models import User, RefreshToken


# ============================================================================
# Repository Interfaces (Protocols)
# ============================================================================

class IUserRepository(Protocol):
    """Interface for user repository."""

    async def create(self, phone_number: str, hashed_password: str) -> User: ...
    async def get_by_phone(self, phone_number: str) -> User | None: ...
    async def get_by_id(self, user_id: str) -> User | None: ...
    async def phone_exists(self, phone_number: str) -> bool: ...
    async def update_last_login(self, user_id: str) -> None: ...
    async def update_password(self, user_id: str, hashed_password: str) -> None: ...


class IRefreshTokenRepository(Protocol):
    """Interface for refresh token repository."""

    async def create(
        self,
        user_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken: ...

    async def get_by_token_id(self, token_id: str) -> RefreshToken | None: ...
    async def revoke(self, token_id: str) -> None: ...
    async def revoke_all_for_user(self, user_id: str) -> None: ...
    async def delete_expired(self) -> int: ...


# ============================================================================
# Repository Implementations
# ============================================================================

class UserRepository:
    """User repository implementation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, phone_number: str, hashed_password: str) -> User:
        """Create new user."""
        user = User(
            phone_number=phone_number,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_phone(self, phone_number: str) -> User | None:
        """Get user by phone number."""
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def phone_exists(self, phone_number: str) -> bool:
        """Check if phone number exists."""
        result = await self.db.execute(
            select(User.id).where(User.phone_number == phone_number)
        )
        return result.first() is not None

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )

    async def update_password(self, user_id: str, hashed_password: str) -> None:
        """Update user's password."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=hashed_password,
                updated_at=datetime.now(timezone.utc)
            )
        )


class RefreshTokenRepository:
    """Refresh token repository implementation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Create new refresh token."""
        token = RefreshToken(
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            token_id=token_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_by_token_id(self, token_id: str) -> RefreshToken | None:
        """Get refresh token by token_id."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_id == token_id,
                RefreshToken.revoked_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: str) -> None:
        """Revoke a refresh token."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_id == token_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user (e.g., after password change)."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )

    async def delete_expired(self) -> int:
        """Delete expired tokens (cleanup job). Returns count deleted."""
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        return result.rowcount


