"""FastAPI dependencies for auth feature."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import verify_access_token
from core.exceptions import InvalidTokenException, TokenExpiredException
from features.auth.models import User
from features.auth.repository import RefreshTokenRepository
from features.users.repository import UserRepository
from features.auth.auth_services import AuthService

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================================
# Repository Dependencies
# ============================================================================

def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


def get_refresh_token_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> RefreshTokenRepository:
    """Get refresh token repository."""
    return RefreshTokenRepository(db)


# ============================================================================
# Service Dependencies
# ============================================================================

def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> AuthService:
    """Get auth service with dependencies injected."""
    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
    )


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token
        payload = verify_access_token(credentials.credentials)

        # Get user
        user = await user_repo.get_by_id(payload["user_id"])

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account deactivated",
            )

        return user

    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type alias for convenience
CurrentUser = Annotated[User, Depends(get_current_user)]


# ============================================================================
# Error Handler Helper
# ============================================================================

def handle_auth_exception(exc: Exception) -> HTTPException:
    """Convert app exceptions to HTTP exceptions."""
    from core.exceptions import (
        AppException,
        PhoneAlreadyExistsException,
        InvalidCredentialsException,
        AccountDeactivatedException,
        PasswordTooWeakException,
        RateLimitExceededException,
    )

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
