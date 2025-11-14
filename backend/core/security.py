"""Security utilities: JWT, password hashing, phone validation, rate limiting."""
import re
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Dict
from collections import defaultdict
import jwt
import bcrypt
from core.config import get_settings
from core.exceptions import (
    PasswordTooWeakException,
    InvalidTokenException,
    TokenExpiredException,
    RateLimitExceededException,
)

settings = get_settings()


# ============================================================================
# Phone Number Handling
# ============================================================================

def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number - just clean up formatting.

    Accepts any phone number format, removes spaces and special characters.
    """
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # Just return as-is, no validation
    return cleaned if cleaned else phone


def validate_phone_number(phone: str) -> bool:
    """Phone validation disabled - accepts any phone number."""
    return True  # Always return True, no validation


# ============================================================================
# Password Handling
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def validate_password_strength(password: str) -> None:
    """
    Validate password meets security requirements.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - Maximum 128 characters (prevent bcrypt DoS)

    Raises PasswordTooWeakException if invalid.
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise PasswordTooWeakException(
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        )

    if len(password) > 128:
        raise PasswordTooWeakException("Password too long (max 128 characters)")

    if not re.search(r'[A-Z]', password):
        raise PasswordTooWeakException("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise PasswordTooWeakException("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise PasswordTooWeakException("Password must contain at least one digit")


# ============================================================================
# JWT Token Handling
# ============================================================================

def create_access_token(
    user_id: str,
    phone_number: str,
    is_active: bool,
    company_id: str | None = None,
    role: str = "user"
) -> str:
    """Create JWT access token with multi-tenancy support."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "phone_number": phone_number,
        "is_active": is_active,
        "company_id": company_id,  # NULL for system_admin
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create JWT refresh token.

    Returns:
        (token, token_id) - token to return to client, token_id to store in DB
    """
    import uuid
    token_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user_id,
        "token_id": token_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, token_id


def verify_access_token(token: str) -> Dict:
    """
    Verify and decode access token.

    Returns decoded payload.
    Raises InvalidTokenException or TokenExpiredException.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidTokenException()

    if payload.get("type") != "access":
        raise InvalidTokenException("Not an access token")

    return payload


def verify_refresh_token(token: str) -> Dict:
    """
    Verify and decode refresh token.

    Returns decoded payload.
    Raises InvalidTokenException or TokenExpiredException.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidTokenException()

    if payload.get("type") != "refresh":
        raise InvalidTokenException("Not a refresh token")

    return payload


# ============================================================================
# Token Hashing for Storage
# ============================================================================

def hash_token(token: str) -> str:
    """
    Hash token for storage using HMAC-SHA256.

    Uses server secret to prevent rainbow table attacks if DB leaks.
    """
    return hmac.new(
        settings.JWT_SECRET_KEY.encode('utf-8'),
        token.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


# ============================================================================
# Rate Limiting (In-Memory - Phase 1)
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter for login attempts."""

    def __init__(self):
        # Store: {phone_number: [(timestamp1, timestamp2, ...)]}
        self._attempts: Dict[str, list[datetime]] = defaultdict(list)

    def check_rate_limit(self, phone_number: str) -> None:
        """
        Check if phone number has exceeded rate limit.

        Raises RateLimitExceededException if limit exceeded.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES)

        # Clean old attempts
        self._attempts[phone_number] = [
            ts for ts in self._attempts[phone_number]
            if ts > window_start
        ]

        # Check if limit exceeded
        if len(self._attempts[phone_number]) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
            # Calculate retry_after
            oldest_attempt = min(self._attempts[phone_number])
            retry_after = int((oldest_attempt - window_start).total_seconds())
            raise RateLimitExceededException(retry_after=max(retry_after, 60))

        # Record this attempt
        self._attempts[phone_number].append(now)

    def reset(self, phone_number: str) -> None:
        """Reset rate limit for phone number (call on successful login)."""
        if phone_number in self._attempts:
            del self._attempts[phone_number]


# Global rate limiter instance
rate_limiter = RateLimiter()
