"""Business logic for authentication."""
import uuid
from datetime import datetime, timedelta, timezone
from features.auth.models import User, RefreshToken
from features.auth.repository import (
    IUserRepository,
    IRefreshTokenRepository,
)
from core.security import (
    normalize_phone_number,
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_token,
    rate_limiter,
)
from core.config import get_settings
from core.exceptions import (
    PhoneAlreadyExistsException,
    InvalidCredentialsException,
    AccountDeactivatedException,
    InvalidTokenException,
    UserNotFoundException,
)

settings = get_settings()


class TokenPair:
    """Token pair response."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    def __init__(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"
        self.expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


class AuthService:
    """Authentication service - handles business logic."""

    user_repo: IUserRepository
    refresh_token_repo: IRefreshTokenRepository

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
    ) -> None:
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    async def signup(self, phone_number: str, password: str) -> tuple[User, TokenPair]:
        """
        Register new user.

        First user becomes system_admin automatically.
        Subsequent signups are not allowed (only system_admin can create users).

        Returns:
            (User, TokenPair)

        Raises:
            PhoneAlreadyExistsException: Phone already registered
            PasswordTooWeakException: Password doesn't meet requirements
            ValueError: If trying to signup after first user (use admin endpoints)
        """
        # 1. Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)

        # 2. Check if phone exists
        if await self.user_repo.phone_exists(normalized_phone):
            raise PhoneAlreadyExistsException()

        # 3. Check if this is the first user
        user_count = await self.user_repo.count_users()

        if user_count > 0:
            # After first user, only system_admin can create users via admin endpoints
            raise ValueError(
                "Public signup is disabled. Please contact system administrator to create your account."
            )

        # 4. Validate password strength
        validate_password_strength(password)

        # 5. Hash password
        hashed_pw = hash_password(password)

        # 6. Create first user as system_admin (no company)
        user = await self.user_repo.create(
            phone_number=normalized_phone,
            hashed_password=hashed_pw,
            company_id=None,  # System admin has no company
            role="system_admin",
        )

        # 7. Generate tokens
        tokens = await self._generate_token_pair(user)

        return user, tokens

    async def login(self, phone_number: str, password: str) -> tuple[User, TokenPair]:
        """
        Login user.

        Returns:
            (User, TokenPair)

        Raises:
            InvalidCredentialsException: Invalid phone or password
            AccountDeactivatedException: Account deactivated
            RateLimitExceededException: Too many failed attempts
        """
        # 1. Normalize phone
        normalized_phone = normalize_phone_number(phone_number)

        # 2. Check rate limit
        rate_limiter.check_rate_limit(normalized_phone)

        # 3. Get user by phone
        user = await self.user_repo.get_by_phone(normalized_phone)
        if not user:
            raise InvalidCredentialsException()

        # 4. Verify password
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        # 5. Check if account is active
        if not user.is_active:
            raise AccountDeactivatedException()

        # 6. Reset rate limiter on successful login
        rate_limiter.reset(normalized_phone)

        # 7. Revoke all existing refresh tokens (single device policy)
        await self.refresh_token_repo.revoke_all_for_user(str(user.id))

        # 8. Generate tokens
        tokens = await self._generate_token_pair(user)

        # 9. Update last login timestamp
        await self.user_repo.update_last_login(str(user.id))

        return user, tokens

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.

        Returns:
            TokenPair (new access + refresh tokens)

        Raises:
            InvalidTokenException: Invalid or revoked token
            TokenExpiredException: Token expired
            UserNotFoundException: User not found
        """
        # 1. Verify token signature and expiry
        payload = verify_refresh_token(refresh_token)

        # 2. Get token from DB (check not revoked)
        token_id = payload.get("token_id")
        db_token = await self.refresh_token_repo.get_by_token_id(token_id)

        if not db_token:
            raise InvalidTokenException("Token not found or revoked")

        # 3. Check token not expired (double check)
        if db_token.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenException("Token expired")

        # 4. Get user
        user = await self.user_repo.get_by_id(str(db_token.user_id))
        if not user or not user.is_active:
            raise UserNotFoundException()

        # 5. Revoke old refresh token (one-time use)
        await self.refresh_token_repo.revoke(token_id)

        # 6. Generate new token pair
        tokens = await self._generate_token_pair(user)

        return tokens

    async def logout(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.

        Raises:
            InvalidTokenException: Invalid token
        """
        try:
            # Verify token
            payload = verify_refresh_token(refresh_token)
            token_id = payload.get("token_id")

            # Revoke token
            await self.refresh_token_repo.revoke(token_id)
        except Exception:
            # Fail silently - token might already be invalid/revoked
            pass

    async def get_current_user(self, user_id: str) -> User:
        """
        Get current authenticated user.

        Raises:
            UserNotFoundException: User not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return user

    # ========================================================================
    # Private helper methods
    # ========================================================================

    async def _generate_token_pair(self, user: User) -> TokenPair:
        """Generate access + refresh token pair."""
        # Create access token
        access_token = create_access_token(
            user_id=str(user.id),
            phone_number=user.phone_number,
            is_active=user.is_active,
            company_id=str(user.company_id) if user.company_id else None,
            role=user.role.value,
        )

        # Create refresh token
        refresh_token, token_id = create_refresh_token(user_id=str(user.id))

        # Hash and store refresh token
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.refresh_token_repo.create(
            user_id=str(user.id),
            token_id=token_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )
