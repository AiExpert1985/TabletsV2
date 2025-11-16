"""Tests for core security functions - password hashing, JWT, rate limiting."""
import pytest
import time
from datetime import datetime, timedelta, timezone

from core.security import (
    normalize_phone_number,
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    hash_token,
    RateLimiter,
)
from core.exceptions import (
    PasswordTooWeakException,
    InvalidTokenException,
    TokenExpiredException,
    RateLimitExceededException,
)


# ============================================================================
# Test Phone Normalization
# ============================================================================

class TestPhoneNormalization:
    """Test phone number normalization."""

    def test_normalize_removes_spaces(self):
        """Normalize removes spaces from phone number."""
        assert normalize_phone_number("077 000 0000") == "0770000000"

    def test_normalize_removes_dashes(self):
        """Normalize removes dashes from phone number."""
        assert normalize_phone_number("077-000-0000") == "0770000000"

    def test_normalize_removes_parentheses(self):
        """Normalize removes parentheses from phone number."""
        assert normalize_phone_number("(077) 000-0000") == "0770000000"

    def test_normalize_keeps_plus(self):
        """Normalize keeps plus sign."""
        assert normalize_phone_number("+964 770 000 0000") == "+9647700000000"

    def test_normalize_already_clean(self):
        """Normalize doesn't change already clean numbers."""
        assert normalize_phone_number("9647700000000") == "9647700000000"


# ============================================================================
# Test Password Hashing
# ============================================================================

class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_hash(self):
        """Hash password creates bcrypt hash."""
        hashed = hash_password("TestPassword123")

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_different_each_time(self):
        """Hash password uses salt - same password produces different hashes."""
        hash1 = hash_password("SamePassword123")
        hash2 = hash_password("SamePassword123")

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Verify password returns True for correct password."""
        password = "MyPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify password returns False for incorrect password."""
        hashed = hash_password("CorrectPassword123")

        assert verify_password("WrongPassword123", hashed) is False

    def test_hash_verify_roundtrip(self):
        """Hash and verify work together correctly."""
        password = "SecurePassword456"
        hashed = hash_password(password)

        assert verify_password(password, hashed)
        assert not verify_password("DifferentPassword456", hashed)


# ============================================================================
# Test Password Validation
# ============================================================================

class TestPasswordValidation:
    """Test password strength validation."""

    def test_valid_password_passes(self):
        """Valid password passes validation."""
        # Should not raise exception
        validate_password_strength("ValidPass123")

    def test_too_short_fails(self):
        """Password too short fails validation."""
        with pytest.raises(PasswordTooWeakException, match="at least"):
            validate_password_strength("Short1")  # 6 chars

    def test_too_long_fails(self):
        """Password too long fails validation."""
        with pytest.raises(PasswordTooWeakException, match="too long"):
            validate_password_strength("A" * 129 + "a1")  # 131 chars

    def test_no_uppercase_fails(self):
        """Password without uppercase fails."""
        with pytest.raises(PasswordTooWeakException, match="uppercase"):
            validate_password_strength("lowercase123")

    def test_no_lowercase_fails(self):
        """Password without lowercase fails."""
        with pytest.raises(PasswordTooWeakException, match="lowercase"):
            validate_password_strength("UPPERCASE123")

    def test_no_digit_fails(self):
        """Password without digit fails."""
        with pytest.raises(PasswordTooWeakException, match="digit"):
            validate_password_strength("NoDigitsHere")

    def test_minimum_length_passes(self):
        """Password with exactly minimum length passes."""
        validate_password_strength("Valid123")  # Exactly 8 chars


# ============================================================================
# Test JWT Access Tokens
# ============================================================================

class TestAccessTokens:
    """Test JWT access token creation and verification."""

    def test_create_access_token(self):
        """Create access token returns JWT string."""
        token = create_access_token(
            user_id="123",
            phone_number="9647700000000",
            is_active=True,
            company_id="456",
            role="user",
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token_success(self):
        """Verify access token decodes payload correctly."""
        # Create token
        token = create_access_token(
            user_id="user-123",
            phone_number="9647700000000",
            is_active=True,
            company_id="company-456",
            role="user",
        )

        # Verify token
        payload = verify_access_token(token)

        assert payload["user_id"] == "user-123"
        assert payload["phone_number"] == "9647700000000"
        assert payload["is_active"] is True
        assert payload["company_id"] == "company-456"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_verify_access_token_invalid(self):
        """Verify access token raises exception for invalid token."""
        with pytest.raises(InvalidTokenException):
            verify_access_token("invalid.token.here")

    def test_verify_access_token_wrong_type(self):
        """Verify access token raises exception for refresh token."""
        # Create refresh token
        refresh_token, _ = create_refresh_token(user_id="123")

        # Try to verify as access token
        with pytest.raises(InvalidTokenException, match="Not an access token"):
            verify_access_token(refresh_token)

    def test_access_token_system_admin_no_company(self):
        """Access token for system admin has no company_id."""
        token = create_access_token(
            user_id="admin-1",
            phone_number="9647700000000",
            is_active=True,
            company_id=None,  # No company
            role="system_admin",
        )

        payload = verify_access_token(token)
        assert payload["company_id"] is None
        assert payload["role"] == "system_admin"


# ============================================================================
# Test JWT Refresh Tokens
# ============================================================================

class TestRefreshTokens:
    """Test JWT refresh token creation and verification."""

    def test_create_refresh_token(self):
        """Create refresh token returns token and token_id."""
        token, token_id = create_refresh_token(user_id="123")

        assert isinstance(token, str)
        assert isinstance(token_id, str)
        assert len(token) > 0
        assert len(token_id) > 0

    def test_create_refresh_token_unique(self):
        """Create refresh token generates unique tokens."""
        token1, id1 = create_refresh_token(user_id="123")
        token2, id2 = create_refresh_token(user_id="123")

        assert token1 != token2
        assert id1 != id2

    def test_verify_refresh_token_success(self):
        """Verify refresh token decodes payload correctly."""
        # Create token
        token, token_id = create_refresh_token(user_id="user-123")

        # Verify token
        payload = verify_refresh_token(token)

        assert payload["user_id"] == "user-123"
        assert payload["token_id"] == token_id
        assert payload["type"] == "refresh"

    def test_verify_refresh_token_invalid(self):
        """Verify refresh token raises exception for invalid token."""
        with pytest.raises(InvalidTokenException):
            verify_refresh_token("invalid.token.here")

    def test_verify_refresh_token_wrong_type(self):
        """Verify refresh token raises exception for access token."""
        # Create access token
        access_token = create_access_token(
            user_id="123",
            phone_number="9647700000000",
            is_active=True,
        )

        # Try to verify as refresh token
        with pytest.raises(InvalidTokenException, match="Not a refresh token"):
            verify_refresh_token(access_token)


# ============================================================================
# Test Token Hashing
# ============================================================================

class TestTokenHashing:
    """Test token hashing for storage."""

    def test_hash_token_creates_hash(self):
        """Hash token creates HMAC-SHA256 hash."""
        token = "some-token-value"
        hashed = hash_token(token)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex digest

    def test_hash_token_deterministic(self):
        """Hash token produces same hash for same input."""
        token = "same-token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_hash_token_different_for_different_input(self):
        """Hash token produces different hashes for different inputs."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")

        assert hash1 != hash2


# ============================================================================
# Test Rate Limiting
# ============================================================================

class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def limiter(self):
        """Create fresh rate limiter for each test."""
        return RateLimiter()

    def test_first_attempt_allowed(self, limiter):
        """First login attempt is allowed."""
        # Should not raise exception
        limiter.check_rate_limit("9647700000000")

    def test_within_limit_allowed(self, limiter):
        """Attempts within limit are allowed."""
        phone = "9647700000000"

        # 5 attempts allowed by default
        for _ in range(5):
            limiter.check_rate_limit(phone)

    def test_exceeds_limit_blocked(self, limiter):
        """Exceeding limit raises exception."""
        phone = "9647700000000"

        # First 5 attempts OK
        for _ in range(5):
            limiter.check_rate_limit(phone)

        # 6th attempt blocked
        with pytest.raises(RateLimitExceededException):
            limiter.check_rate_limit(phone)

    def test_reset_clears_attempts(self, limiter):
        """Reset clears attempts for phone number."""
        phone = "9647700000000"

        # Make some attempts
        for _ in range(5):
            limiter.check_rate_limit(phone)

        # Reset
        limiter.reset(phone)

        # Should be able to attempt again
        limiter.check_rate_limit(phone)

    def test_different_phones_independent(self, limiter):
        """Different phone numbers have independent rate limits."""
        phone1 = "9647700000001"
        phone2 = "9647700000002"

        # Max out phone1
        for _ in range(5):
            limiter.check_rate_limit(phone1)

        # phone2 should still work
        limiter.check_rate_limit(phone2)

    def test_rate_limit_exception_has_retry_after(self, limiter):
        """RateLimitExceededException includes retry_after."""
        phone = "9647700000000"

        # Max out attempts
        for _ in range(5):
            limiter.check_rate_limit(phone)

        # Check exception has retry_after
        with pytest.raises(RateLimitExceededException) as exc_info:
            limiter.check_rate_limit(phone)

        assert exc_info.value.retry_after > 0
