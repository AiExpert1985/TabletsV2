"""FastAPI routes for authentication."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from features.auth.schemas import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    ChangePasswordRequest,
    UserResponse,
    MessageResponse,
)
from features.auth.services import AuthService
from features.auth.dependencies import get_auth_service, CurrentUser
from core.exceptions import (
    AppException,
    PhoneAlreadyExistsException,
    InvalidCredentialsException,
    AccountDeactivatedException,
    PasswordTooWeakException,
    RateLimitExceededException,
    ResetTokenInvalidException,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Error Handler Helper
# ============================================================================

def handle_auth_exception(exc: Exception) -> HTTPException:
    """Convert app exceptions to HTTP exceptions."""
    if isinstance(exc, PhoneAlreadyExistsException):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, InvalidCredentialsException):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, AccountDeactivatedException):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, PasswordTooWeakException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, RateLimitExceededException):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": exc.code, "message": exc.message},
            headers={"Retry-After": str(exc.retry_after)},
        )
    elif isinstance(exc, ResetTokenInvalidException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, AppException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        )
    elif isinstance(exc, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(exc)},
        )
    else:
        # Unknown error
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
        )


# ============================================================================
# Routes
# ============================================================================

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Register a new user.

    - **phone_number**: Iraqi mobile number (e.g., 07501234567 or +9647501234567)
    - **password**: Minimum 8 characters, must contain uppercase, lowercase, and digit
    - **password_confirm**: Must match password
    """
    # DEBUG: Log incoming request
    print(f"[DEBUG] Signup request received:")
    print(f"  phone_number: {request.phone_number} (length: {len(request.phone_number)})")
    print(f"  password length: {len(request.password)}")
    print(f"  password_confirm length: {len(request.password_confirm)}")

    try:
        user, tokens = await auth_service.signup(
            phone_number=request.phone_number,
            password=request.password,
        )

        return SignupResponse(
            user=UserResponse(
                id=str(user.id),
                phone_number=user.phone_number,
                email=user.email,
                is_active=user.is_active,
                is_phone_verified=user.is_phone_verified,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )
    except Exception as exc:
        print(f"[DEBUG] Signup error: {type(exc).__name__}: {str(exc)}")
        raise handle_auth_exception(exc)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Login with phone number and password.

    - **phone_number**: Registered phone number
    - **password**: Account password

    Note: Limited to 5 attempts per hour per phone number.
    """
    try:
        user, tokens = await auth_service.login(
            phone_number=request.phone_number,
            password=request.password,
        )

        return LoginResponse(
            user=UserResponse(
                id=str(user.id),
                phone_number=user.phone_number,
                email=user.email,
                is_active=user.is_active,
                is_phone_verified=user.is_phone_verified,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )
    except Exception as exc:
        raise handle_auth_exception(exc)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Refresh access token using refresh token.

    Returns new access token and refresh token pair.
    Old refresh token is invalidated (one-time use).
    """
    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except Exception as exc:
        raise handle_auth_exception(exc)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Logout by revoking refresh token.

    Refresh token will no longer be valid after this call.
    """
    await auth_service.logout(request.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header:
    `Authorization: Bearer <access_token>`
    """
    return UserResponse(
        id=str(current_user.id),
        phone_number=current_user.phone_number,
        email=current_user.email,
        is_active=current_user.is_active,
        is_phone_verified=current_user.is_phone_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/password/request-reset", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequestSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Request password reset.

    Sends reset code to registered phone number via SMS (if phone exists).
    Always returns success message for security (prevent enumeration).

    Note: Phase 1 logs reset token to console. Phase 2 will send via SMS.
    """
    try:
        reset_token = await auth_service.request_password_reset(request.phone_number)
        # TODO Phase 2: Remove this logging, only send via SMS
        if reset_token:
            print(f"[DEV] Password reset token: {reset_token}")

        return MessageResponse(
            message="If the phone number is registered, a reset code has been sent"
        )
    except Exception as exc:
        # Always return success to prevent enumeration
        return MessageResponse(
            message="If the phone number is registered, a reset code has been sent"
        )


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Reset password using reset token.

    - **reset_token**: Token received via SMS
    - **new_password**: New password (must meet requirements)
    - **new_password_confirm**: Must match new_password

    Note: Token valid for 15 minutes and single-use only.
    """
    try:
        await auth_service.reset_password(
            reset_token=request.reset_token,
            new_password=request.new_password,
        )
        return MessageResponse(message="Password reset successful")
    except Exception as exc:
        raise handle_auth_exception(exc)


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """
    Change password (while authenticated).

    Requires valid access token.

    - **old_password**: Current password
    - **new_password**: New password (must meet requirements)
    - **new_password_confirm**: Must match new_password

    Note: All active sessions will be logged out after password change.
    """
    try:
        await auth_service.change_password(
            user_id=str(current_user.id),
            old_password=request.old_password,
            new_password=request.new_password,
        )
        return MessageResponse(message="Password changed successfully")
    except Exception as exc:
        raise handle_auth_exception(exc)
