"""Repository layer for users feature - data access operations."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.models import User


class UserRepository:
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
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(User)
            .where(User.phone_number == phone_number)
            .options(selectinload(User.company))  # Eagerly load company for status check
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.company))  # Eagerly load company for status check
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

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users (system admin only)."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .options(selectinload(User.company))  # Eagerly load company for status check
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
