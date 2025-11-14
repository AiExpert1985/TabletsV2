"""Business logic for authentication."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol
from features.auth.models import User, RefreshToken
from features.auth.repository import (
    IUserRepository,
    IRefreshTokenRepository,
    IPasswordResetRepository,
)
from features.auth.notifications import INotificationService
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
    ResetTokenInvalidException,
    ResetTokenExpiredException,
)

settings = get_settings()


class TokenPair:
    """Token pair response."""

    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"
        self.expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


class AuthService:
    """Authentication service - handles business logic."""

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_reset_repo: IPasswordResetRepository,
        notification_service: INotificationService | None = None,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.password_reset_repo = password_reset_repo
        self.notification_service = notification_service

    async def signup(self, phone_number: str, password: str) -> tuple[User, TokenPair]:
        """
        Register new user.

        Returns:
            (User, TokenPair)

        Raises:
            PhoneAlreadyExistsException: Phone already registered
            PasswordTooWeakException: Password doesn't meet requirements
        """
        # 1. Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)

        # 2. Check if phone exists
        if await self.user_repo.phone_exists(normalized_phone):
            raise PhoneAlreadyExistsException()

        # 3. Validate password strength
        validate_password_strength(password)

        # 4. Hash password
        hashed_pw = hash_password(password)

        # 5. Create user
        user = await self.user_repo.create(
            phone_number=normalized_phone,
            hashed_password=hashed_pw,
        )

        # 6. Generate tokens
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

    async def request_password_reset(self, phone_number: str) -> str:
        """
        Request password reset.

        Returns:
            Reset token (plain text - to be sent via SMS/email)

        Note: Fails silently if phone not found (security: prevent enumeration)
        """
        # 1. Normalize phone
        try:
            normalized_phone = normalize_phone_number(phone_number)
        except ValueError:
            # Invalid phone format - fail silently
            return ""

        # 2. Get user by phone
        user = await self.user_repo.get_by_phone(normalized_phone)
        if not user:
            # Fail silently - don't reveal if phone exists
            return ""

        # 3. Invalidate all existing reset tokens for user
        await self.password_reset_repo.invalidate_all_for_user(str(user.id))

        # 4. Generate reset token (plain UUID)
        reset_token = str(uuid.uuid4())

        # 5. Hash token for storage
        token_hash = hash_token(reset_token)

        # 6. Store in DB with 15 min expiry
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        await self.password_reset_repo.create(
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # 7. Send notification (SMS/Email)
        if self.notification_service:
            message = f"Your password reset code is: {reset_token}\n\nThis code expires in 15 minutes."
            await self.notification_service.send(
                recipient=user.phone_number,
                message=message,
            )

        # Return token (for development - in production, only send via SMS/email)
        # TODO Phase 2: Don't return token, only send via notification
        return reset_token

    async def reset_password(self, reset_token: str, new_password: str) -> None:
        """
        Reset password using reset token.

        Raises:
            ResetTokenInvalidException: Invalid or already used token
            ResetTokenExpiredException: Token expired
            PasswordTooWeakException: Password doesn't meet requirements
        """
        # 1. Validate new password
        validate_password_strength(new_password)

        # 2. Hash token
        token_hash = hash_token(reset_token)

        # 3. Get valid token from DB
        db_token = await self.password_reset_repo.get_valid_token(token_hash)

        if not db_token:
            # Could be invalid, expired, or already used
            raise ResetTokenInvalidException()

        # 4. Get user
        user = await self.user_repo.get_by_id(str(db_token.user_id))
        if not user:
            raise UserNotFoundException()

        # 5. Hash new password
        hashed_pw = hash_password(new_password)

        # 6. Update user password
        await self.user_repo.update_password(str(user.id), hashed_pw)

        # 7. Mark token as used
        await self.password_reset_repo.mark_used(str(db_token.id))

        # 8. Revoke all refresh tokens (force re-login on all devices)
        await self.refresh_token_repo.revoke_all_for_user(str(user.id))

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Change password (while authenticated).

        Raises:
            UserNotFoundException: User not found
            InvalidCredentialsException: Old password incorrect
            PasswordTooWeakException: New password doesn't meet requirements
        """
        # 1. Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        # 2. Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsException()

        # 3. Validate new password
        validate_password_strength(new_password)

        # 4. Hash new password
        hashed_pw = hash_password(new_password)

        # 5. Update password
        await self.user_repo.update_password(user_id, hashed_pw)

        # 6. Revoke all refresh tokens (force re-login)
        await self.refresh_token_repo.revoke_all_for_user(user_id)

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
