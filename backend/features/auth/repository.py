"""Repository layer for auth feature - abstracts database operations."""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.models import User, RefreshToken


# ============================================================================
# Repository Interfaces (Abstract Base Classes)
# ============================================================================

class IUserRepository(ABC):
    """Interface for user repository."""

    @abstractmethod
    async def create(
        self,
        phone_number: str,
        hashed_password: str,
        company_id: str | None = None,
        role: str = "user"
    ) -> User:
        """Create new user."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user model to database."""
        pass

    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> User | None:
        """Get user by phone number."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        pass

    @abstractmethod
    async def phone_exists(self, phone_number: str) -> bool:
        """Check if phone number exists."""
        pass

    @abstractmethod
    async def count_users(self) -> int:
        """Count total users."""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        pass

    @abstractmethod
    async def update_password(self, user_id: str, hashed_password: str) -> None:
        """Update user's password."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user."""
        pass

    @abstractmethod
    async def delete(self, user: User) -> None:
        """Delete a user."""
        pass


class IRefreshTokenRepository(ABC):
    """Interface for refresh token repository."""

    @abstractmethod
    async def create(
        self,
        user_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Create new refresh token."""
        pass

    @abstractmethod
    async def get_by_token_id(self, token_id: str) -> RefreshToken | None:
        """Get refresh token by token_id."""
        pass

    @abstractmethod
    async def revoke(self, token_id: str) -> None:
        """Revoke a refresh token."""
        pass

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        pass


# ============================================================================
# Repository Implementations
# ============================================================================

class UserRepository(IUserRepository):
    """User repository implementation."""

    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        phone_number: str,
        hashed_password: str,
        company_id: str | None = None,
        role: str = "user"
    ) -> User:
        """Create new user with multi-tenancy support."""
        from features.auth.models import UserRole
        user = User(
            phone_number=phone_number,
            hashed_password=hashed_password,
            company_id=uuid.UUID(company_id) if company_id else None,
            role=UserRole(role),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def save(self, user: User) -> User:
        """Save user model to database."""
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

    async def count_users(self) -> int:
        """Count total users in the system."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(User.id))
        )
        return result.scalar() or 0

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

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users (system admin only)."""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """Update user."""
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.db.delete(user)
        await self.db.flush()


class RefreshTokenRepository(IRefreshTokenRepository):
    """Refresh token repository implementation."""

    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
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


