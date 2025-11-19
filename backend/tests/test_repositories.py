"""Tests for repository layer - database operations."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from features.users.models import User
from core.enums import UserRole
from features.users.repository import UserRepository
from features.auth.repository import RefreshTokenRepository
from features.company.models import Company
from features.company.repository import CompanyRepository
from core.security import hash_password


# ============================================================================
# Test UserRepository
# ============================================================================

class TestUserRepository:
    """Test UserRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_user(
        self,
        user_repo: UserRepository,
        test_company: Company,
    ):
        """Create user stores user in database."""
        # Act
        user = await user_repo.create(
            name="Test User",
            phone_number="9647700000010",
            hashed_password=hash_password("TestPass123"),
            company_id=str(test_company.id),
            role="viewer",
        )

        # Assert
        assert user.id is not None
        assert user.phone_number == "9647700000010"
        assert user.company_id == test_company.id
        assert user.role == UserRole.VIEWER
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_create_system_admin(
        self,
        user_repo: UserRepository,
    ):
        """Create system admin with no company."""
        # Act
        user = await user_repo.create(
            name="System Admin",
            phone_number="9647700000020",
            hashed_password=hash_password("AdminPass123"),
            company_id=None,
            role="system_admin",
        )

        # Assert
        assert user.company_id is None
        assert user.role == UserRole.SYSTEM_ADMIN

    @pytest.mark.asyncio
    async def test_get_by_phone_found(
        self,
        user_repo: UserRepository,
        test_user: User,
    ):
        """Get by phone returns user when exists."""
        # Act
        user = await user_repo.get_by_phone(test_user.phone_number)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.phone_number == test_user.phone_number

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(
        self,
        user_repo: UserRepository,
    ):
        """Get by phone returns None when not exists."""
        # Act
        user = await user_repo.get_by_phone("9647799999999")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self,
        user_repo: UserRepository,
        test_user: User,
    ):
        """Get by ID returns user when exists."""
        # Act
        user = await user_repo.get_by_id(str(test_user.id))

        # Assert
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        user_repo: UserRepository,
    ):
        """Get by ID returns None when not exists."""
        # Act
        user = await user_repo.get_by_id("00000000-0000-0000-0000-000000000000")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_phone_exists_true(
        self,
        user_repo: UserRepository,
        test_user: User,
    ):
        """Phone exists returns True when phone exists."""
        # Act
        exists = await user_repo.phone_exists(test_user.phone_number)

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    async def test_phone_exists_false(
        self,
        user_repo: UserRepository,
    ):
        """Phone exists returns False when phone doesn't exist."""
        # Act
        exists = await user_repo.phone_exists("9647799999999")

        # Assert
        assert exists is False

    @pytest.mark.asyncio
    async def test_count_users(
        self,
        user_repo: UserRepository,
        test_user: User,
        test_admin_user: User,
    ):
        """Count users returns total number of users."""
        # Act
        count = await user_repo.count_users()

        # Assert
        assert count >= 2  # At least our test users

    @pytest.mark.asyncio
    async def test_update_last_login(
        self,
        user_repo: UserRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Update last login updates timestamp."""
        # Arrange
        original_last_login = test_user.last_login_at

        # Act
        await user_repo.update_last_login(str(test_user.id))
        await db_session.flush()  # Flush to make changes visible

        # Refresh user object
        await db_session.refresh(test_user)

        # Assert
        assert test_user.last_login_at != original_last_login
        assert test_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_get_all_pagination(
        self,
        user_repo: UserRepository,
        test_user: User,
        test_admin_user: User,
    ):
        """Get all supports pagination."""
        # Act
        users_page1 = await user_repo.get_all(skip=0, limit=1)
        users_page2 = await user_repo.get_all(skip=1, limit=1)

        # Assert
        assert len(users_page1) == 1
        assert len(users_page2) >= 1
        if len(users_page2) > 0:
            assert users_page1[0].id != users_page2[0].id

    @pytest.mark.asyncio
    async def test_update_user(
        self,
        user_repo: UserRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Update user persists changes."""
        # Arrange
        test_user.is_active = False

        # Act
        await user_repo.update(test_user)
        await db_session.commit()

        # Fetch fresh user
        updated_user = await user_repo.get_by_id(str(test_user.id))
        assert updated_user is not None, "User should exist after update"

        # Assert changes
        assert updated_user.is_active is False

    @pytest.mark.asyncio
    async def test_delete_user(
        self,
        user_repo: UserRepository,
        test_company: Company,
        db_session: AsyncSession,
    ):
        """Delete user removes user from database."""
        # Arrange - create user to delete
        user = await user_repo.create(
            name="Test User",
            phone_number="9647700000099",
            hashed_password=hash_password("Test123"),
            company_id=str(test_company.id),
            role="viewer",
        )
        user_id = str(user.id)
        await db_session.commit()

        # Act
        await user_repo.delete(user)
        await db_session.commit()

        # Assert
        deleted_user = await user_repo.get_by_id(user_id)
        assert deleted_user is None


# ============================================================================
# Test RefreshTokenRepository
# ============================================================================

class TestRefreshTokenRepository:
    """Test RefreshTokenRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_token(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
    ):
        """Create token stores token in database."""
        # Arrange
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Act
        token = await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="test-token-id-123",
            token_hash="test-hash-123",
            expires_at=expires_at,
        )

        # Assert
        assert token.id is not None
        assert token.user_id == test_user.id
        assert token.token_id == "test-token-id-123"
        assert token.token_hash == "test-hash-123"
        assert token.revoked_at is None

    @pytest.mark.asyncio
    async def test_get_by_token_id_found(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
    ):
        """Get by token_id returns token when exists and not revoked."""
        # Arrange
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        created_token = await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="find-me-123",
            token_hash="hash-123",
            expires_at=expires_at,
        )

        # Act
        found_token = await refresh_token_repo.get_by_token_id("find-me-123")

        # Assert
        assert found_token is not None
        assert found_token.id == created_token.id

    @pytest.mark.asyncio
    async def test_get_by_token_id_not_found(
        self,
        refresh_token_repo: RefreshTokenRepository,
    ):
        """Get by token_id returns None when not exists."""
        # Act
        token = await refresh_token_repo.get_by_token_id("nonexistent")

        # Assert
        assert token is None

    @pytest.mark.asyncio
    async def test_get_by_token_id_revoked_not_found(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Get by token_id returns None for revoked tokens."""
        # Arrange
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="revoked-token",
            token_hash="hash",
            expires_at=expires_at,
        )

        # Revoke it
        await refresh_token_repo.revoke("revoked-token")
        await db_session.commit()

        # Act
        token = await refresh_token_repo.get_by_token_id("revoked-token")

        # Assert
        assert token is None

    @pytest.mark.asyncio
    async def test_revoke_sets_timestamp(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Revoke sets revoked_at timestamp."""
        # Arrange
        from datetime import timedelta
        from sqlalchemy import select
        from features.auth.models import RefreshToken

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="to-revoke",
            token_hash="hash",
            expires_at=expires_at,
        )

        # Act
        await refresh_token_repo.revoke("to-revoke")
        await db_session.commit()

        # Fetch directly (bypassing get_by_token_id which filters revoked)
        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token_id == "to-revoke")
        )
        token = result.scalar_one_or_none()

        # Assert
        assert token is not None
        assert token.revoked_at is not None

    @pytest.mark.asyncio
    async def test_revoke_all_for_user(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Revoke all for user revokes all user's tokens."""
        # Arrange
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Create multiple tokens
        await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="token1",
            token_hash="hash1",
            expires_at=expires_at,
        )
        await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="token2",
            token_hash="hash2",
            expires_at=expires_at,
        )

        # Act
        await refresh_token_repo.revoke_all_for_user(str(test_user.id))
        await db_session.commit()

        # Assert
        token1 = await refresh_token_repo.get_by_token_id("token1")
        token2 = await refresh_token_repo.get_by_token_id("token2")
        assert token1 is None
        assert token2 is None

    @pytest.mark.asyncio
    async def test_delete_expired(
        self,
        refresh_token_repo: RefreshTokenRepository,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Delete expired removes expired tokens."""
        # Arrange
        from datetime import timedelta
        past = datetime.now(timezone.utc) - timedelta(days=1)

        # Create expired token
        await refresh_token_repo.create(
            user_id=str(test_user.id),
            token_id="expired-token",
            token_hash="hash",
            expires_at=past,  # Already expired
        )
        await db_session.commit()

        # Act
        deleted_count = await refresh_token_repo.delete_expired()
        await db_session.commit()

        # Assert
        assert deleted_count >= 1


# ============================================================================
# Test CompanyRepository
# ============================================================================

class TestCompanyRepository:
    """Test CompanyRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_company(
        self,
        company_repo: CompanyRepository,
    ):
        """Create company stores company in database."""
        # Act
        company = await company_repo.create(name="Test Company Inc")

        # Assert
        assert company.id is not None
        assert company.name == "Test Company Inc"
        assert company.is_active is True
        assert company.created_at is not None

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self,
        company_repo: CompanyRepository,
        test_company: Company,
    ):
        """Get by ID returns company when exists."""
        # Act
        company = await company_repo.get_by_id(str(test_company.id))

        # Assert
        assert company is not None
        assert company.id == test_company.id
        assert company.name == test_company.name

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        company_repo: CompanyRepository,
    ):
        """Get by ID returns None when not exists."""
        # Act
        company = await company_repo.get_by_id("00000000-0000-0000-0000-000000000000")

        # Assert
        assert company is None

    @pytest.mark.asyncio
    async def test_get_by_name_found(
        self,
        company_repo: CompanyRepository,
        test_company: Company,
    ):
        """Get by name returns company when exists."""
        # Act
        company = await company_repo.get_by_name(test_company.name)

        # Assert
        assert company is not None
        assert company.id == test_company.id

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self,
        company_repo: CompanyRepository,
    ):
        """Get by name returns None when not exists."""
        # Act
        company = await company_repo.get_by_name("Nonexistent Company")

        # Assert
        assert company is None

    @pytest.mark.asyncio
    async def test_get_all_pagination(
        self,
        company_repo: CompanyRepository,
        test_company: Company,
    ):
        """Get all returns companies with pagination."""
        # Act
        companies = await company_repo.get_all(skip=0, limit=10)

        # Assert
        assert len(companies) >= 1
        assert any(c.id == test_company.id for c in companies)

    @pytest.mark.asyncio
    async def test_update_name(
        self,
        company_repo: CompanyRepository,
        test_company: Company,
        db_session: AsyncSession,
    ):
        """Update company name works."""
        # Act
        updated = await company_repo.update(
            company_id=str(test_company.id),
            name="Updated Company Name",
        )
        await db_session.flush()  # Flush to make changes visible
        db_session.expire_all()  # Expire all cached objects

        # Refresh to get latest data
        await db_session.refresh(updated)

        # Assert
        assert updated is not None
        assert updated.name == "Updated Company Name"
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_is_active(
        self,
        company_repo: CompanyRepository,
        test_company: Company,
        db_session: AsyncSession,
    ):
        """Update company is_active works."""
        # Act
        updated = await company_repo.update(
            company_id=str(test_company.id),
            is_active=False,
        )
        await db_session.flush()  # Flush to make changes visible
        db_session.expire_all()  # Expire all cached objects

        # Refresh to get latest data
        await db_session.refresh(updated)

        # Assert
        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_delete_company(
        self,
        company_repo: CompanyRepository,
        db_session: AsyncSession,
    ):
        """Delete company removes company from database."""
        # Arrange
        company = await company_repo.create(name="To Delete")
        company_id = str(company.id)
        await db_session.commit()

        # Act
        deleted = await company_repo.delete(company_id)
        await db_session.commit()

        # Assert
        assert deleted is True
        found = await company_repo.get_by_id(company_id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(
        self,
        company_repo: CompanyRepository,
    ):
        """Delete nonexistent company returns False."""
        # Act
        deleted = await company_repo.delete("00000000-0000-0000-0000-000000000000")

        # Assert
        assert deleted is False
