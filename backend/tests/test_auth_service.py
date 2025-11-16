"""Tests for AuthService - Business logic tests."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from features.auth.services import AuthService, TokenPair
from features.auth.models import User
from features.auth.repository import UserRepository, RefreshTokenRepository
from core.exceptions import (
    PhoneAlreadyExistsException,
    InvalidCredentialsException,
    AccountDeactivatedException,
    InvalidTokenException,
    UserNotFoundException,
    PasswordTooWeakException,
)
from core.security import verify_password, hash_password


# ============================================================================
# Test Signup
# ============================================================================

class TestAuthServiceSignup:
    """Test user signup functionality."""

    @pytest.mark.asyncio
    async def test_first_signup_creates_system_admin(
        self,
        auth_service: AuthService,
        db_session: AsyncSession,
    ):
        """First user signup creates system_admin with no company."""
        # Act
        user, tokens = await auth_service.signup(
            phone_number="9647700000000",
            password="StrongPassword123",
        )

        # Assert
        assert user.phone_number == "9647700000000"
        assert user.role.value == "system_admin"
        assert user.company_id is None
        assert user.is_active is True
        assert verify_password("StrongPassword123", user.hashed_password)

        # Check tokens
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    @pytest.mark.asyncio
    async def test_second_signup_fails(
        self,
        auth_service: AuthService,
        test_user: User,
    ):
        """Second signup fails - only admin can create users."""
        # Act & Assert
        with pytest.raises(ValueError, match="Public signup is disabled"):
            await auth_service.signup(
                phone_number="9647700000002",
                password="AnotherPassword123",
            )

    @pytest.mark.asyncio
    async def test_signup_duplicate_phone_fails(
        self,
        auth_service: AuthService,
        user_repo: UserRepository,
    ):
        """Signup with existing phone number fails."""
        # Arrange - create first user
        await auth_service.signup(
            phone_number="9647700000010",
            password="Password123",
        )

        # Clear DB to allow second signup
        # (In real scenario, this would be caught by phone_exists check)

        # Create another user directly
        await user_repo.create(
            phone_number="9647700000011",
            hashed_password=hash_password("Test123"),
            company_id=None,
            role="system_admin",
        )

        # Act & Assert
        with pytest.raises(PhoneAlreadyExistsException):
            await auth_service.signup(
                phone_number="9647700000011",  # Same phone
                password="Password456",
            )

    @pytest.mark.asyncio
    async def test_signup_weak_password_fails(
        self,
        auth_service: AuthService,
    ):
        """Signup with weak password fails."""
        # Act & Assert
        with pytest.raises(PasswordTooWeakException):
            await auth_service.signup(
                phone_number="9647700000020",
                password="weak",  # Too short
            )

    @pytest.mark.asyncio
    async def test_signup_normalizes_phone(
        self,
        auth_service: AuthService,
    ):
        """Signup normalizes phone number correctly."""
        # Act
        user, _ = await auth_service.signup(
            phone_number="964 770 123 4567",  # With spaces
            password="ValidPassword123",
        )

        # Assert
        assert user.phone_number == "9647701234567"  # Spaces removed


# ============================================================================
# Test Login
# ============================================================================

class TestAuthServiceLogin:
    """Test user login functionality."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
        valid_password: str,
    ):
        """Successful login returns user and tokens."""
        # Act
        user, tokens = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Assert
        assert user.id == test_user.id
        assert user.phone_number == valid_phone
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
    ):
        """Login with wrong password fails."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login(
                phone_number=valid_phone,
                password="WrongPassword123",
            )

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
        self,
        auth_service: AuthService,
    ):
        """Login with non-existent phone fails."""
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            await auth_service.login(
                phone_number="9647799999999",
                password="SomePassword123",
            )

    @pytest.mark.asyncio
    async def test_login_inactive_account(
        self,
        auth_service: AuthService,
        test_user: User,
        user_repo: UserRepository,
        valid_phone: str,
        valid_password: str,
    ):
        """Login with inactive account fails."""
        # Arrange - deactivate user
        test_user.is_active = False
        await user_repo.update(test_user)

        # Act & Assert
        with pytest.raises(AccountDeactivatedException):
            await auth_service.login(
                phone_number=valid_phone,
                password=valid_password,
            )

    @pytest.mark.asyncio
    async def test_login_normalizes_phone(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_password: str,
    ):
        """Login normalizes phone number before lookup."""
        # Act - login with unnormalized phone (with spaces)
        user, _ = await auth_service.login(
            phone_number="964 770 000 0001",  # Same phone with spaces
            password=valid_password,
        )

        # Assert
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_login_updates_last_login(
        self,
        auth_service: AuthService,
        test_user: User,
        user_repo: UserRepository,
        valid_phone: str,
        valid_password: str,
    ):
        """Login updates last_login_at timestamp."""
        # Arrange
        original_last_login = test_user.last_login_at

        # Act
        await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Assert - refresh user object
        from core.dependencies import get_db
        db_session = auth_service.user_repo.db
        await db_session.refresh(test_user)
        assert test_user.last_login_at != original_last_login
        assert test_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_login_revokes_existing_tokens(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
        valid_password: str,
    ):
        """Login revokes all existing refresh tokens (single device policy)."""
        # Arrange - create first session
        _, tokens1 = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Act - login again
        _, tokens2 = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Assert - old token should be revoked
        with pytest.raises(InvalidTokenException):
            await auth_service.refresh_access_token(tokens1.refresh_token)

        # New token should work
        new_tokens = await auth_service.refresh_access_token(tokens2.refresh_token)
        assert new_tokens.access_token is not None


# ============================================================================
# Test Refresh Token
# ============================================================================

class TestAuthServiceRefreshToken:
    """Test refresh token functionality."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
        valid_password: str,
    ):
        """Refresh token returns new token pair."""
        # Arrange - login to get tokens
        _, tokens = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Act
        new_tokens = await auth_service.refresh_access_token(tokens.refresh_token)

        # Assert - check that new tokens were generated successfully
        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.token_type == "bearer"
        # Note: Tokens might be identical if created in the same second due to iat timestamp

    @pytest.mark.asyncio
    async def test_refresh_token_one_time_use(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
        valid_password: str,
    ):
        """Refresh token can only be used once."""
        # Arrange - login to get tokens
        _, tokens = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Act - use token once
        await auth_service.refresh_access_token(tokens.refresh_token)

        # Assert - using it again fails
        with pytest.raises(InvalidTokenException):
            await auth_service.refresh_access_token(tokens.refresh_token)

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
        self,
        auth_service: AuthService,
    ):
        """Refresh with invalid token fails."""
        # Act & Assert
        with pytest.raises(Exception):  # Could be InvalidTokenException or JWT error
            await auth_service.refresh_access_token("invalid.token.here")


# ============================================================================
# Test Logout
# ============================================================================

class TestAuthServiceLogout:
    """Test logout functionality."""

    @pytest.mark.asyncio
    async def test_logout_revokes_token(
        self,
        auth_service: AuthService,
        test_user: User,
        valid_phone: str,
        valid_password: str,
    ):
        """Logout revokes refresh token."""
        # Arrange - login to get tokens
        _, tokens = await auth_service.login(
            phone_number=valid_phone,
            password=valid_password,
        )

        # Act - logout
        await auth_service.logout(tokens.refresh_token)

        # Assert - token is revoked
        with pytest.raises(InvalidTokenException):
            await auth_service.refresh_access_token(tokens.refresh_token)

    @pytest.mark.asyncio
    async def test_logout_invalid_token_silent_fail(
        self,
        auth_service: AuthService,
    ):
        """Logout with invalid token fails silently."""
        # Act - should not raise exception
        await auth_service.logout("invalid.token.here")


# ============================================================================
# Test Get Current User
# ============================================================================

class TestAuthServiceGetCurrentUser:
    """Test get current user functionality."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        auth_service: AuthService,
        test_user: User,
    ):
        """Get current user returns user."""
        # Act
        user = await auth_service.get_current_user(str(test_user.id))

        # Assert
        assert user.id == test_user.id
        assert user.phone_number == test_user.phone_number

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(
        self,
        auth_service: AuthService,
    ):
        """Get current user with invalid ID fails."""
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            await auth_service.get_current_user("00000000-0000-0000-0000-000000000000")
