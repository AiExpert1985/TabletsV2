"""Repository layer for auth feature - data access operations."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.models import RefreshToken


class RefreshTokenRepository:
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


