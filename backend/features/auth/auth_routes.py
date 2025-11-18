"""FastAPI routes for authentication."""
from typing import Annotated
from fastapi import APIRouter, Depends
from features.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    MessageResponse,
    UserResponse,
)
from features.auth.auth_services import AuthService
from features.auth.dependencies import (
    get_auth_service,
    CurrentUser,
    build_user_response,
    handle_auth_exception,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Routes
# ============================================================================

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
            user=build_user_response(user),
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
    return build_user_response(current_user)


