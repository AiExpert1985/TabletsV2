"""
FastAPI dependencies for authorization.

Provides permission checking for routes.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from features.auth.dependencies import CurrentUser
from features.authorization.service import AuthorizationService, create_authorization_service
from features.authorization.permissions import Permission
from features.logging.logger import get_logger

logger = get_logger(__name__)


def get_authorization_service(
    current_user: CurrentUser,
) -> AuthorizationService:
    """
    Get authorization service for the current user.

    Dependency for route handlers.

    Args:
        current_user: Currently authenticated user

    Returns:
        AuthorizationService instance
    """
    return create_authorization_service(current_user)


# Type alias for convenience
AuthService = Annotated[AuthorizationService, Depends(get_authorization_service)]


def require_permission(permission: Permission):
    """
    Decorator dependency to require a specific permission.

    Usage:
        @router.get("/users")
        async def get_users(
            auth: Annotated[None, Depends(require_permission(Permission.VIEW_USERS))]
        ):
            ...

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """
    def permission_checker(auth_service: AuthService) -> None:
        """Check if user has the required permission."""
        if not auth_service.has_permission(permission):
            logger.warning(
                f"Permission denied: User {auth_service.user.id if auth_service.user else 'None'} "
                f"attempted to access {permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )

    return Depends(permission_checker)


def require_any_permission(*permissions: Permission):
    """
    Decorator dependency to require ANY of the given permissions.

    Usage:
        @router.get("/dashboard")
        async def dashboard(
            auth: Annotated[None, Depends(require_any_permission(
                Permission.VIEW_REPORTS,
                Permission.VIEW_FINANCIALS
            ))]
        ):
            ...

    Args:
        *permissions: List of acceptable permissions

    Returns:
        Dependency function
    """
    def permission_checker(auth_service: AuthService) -> None:
        """Check if user has any of the required permissions."""
        if not auth_service.has_any_permission(list(permissions)):
            logger.warning(
                f"Permission denied: User {auth_service.user.id if auth_service.user else 'None'} "
                f"needs one of: {[p.value for p in permissions]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of {[p.value for p in permissions]}"
            )

    return Depends(permission_checker)


def require_all_permissions(*permissions: Permission):
    """
    Decorator dependency to require ALL of the given permissions.

    Usage:
        @router.post("/admin-action")
        async def admin_action(
            auth: Annotated[None, Depends(require_all_permissions(
                Permission.VIEW_USERS,
                Permission.EDIT_USERS
            ))]
        ):
            ...

    Args:
        *permissions: List of required permissions

    Returns:
        Dependency function
    """
    def permission_checker(auth_service: AuthService) -> None:
        """Check if user has all of the required permissions."""
        if not auth_service.has_all_permissions(list(permissions)):
            logger.warning(
                f"Permission denied: User {auth_service.user.id if auth_service.user else 'None'} "
                f"needs all of: {[p.value for p in permissions]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires all of {[p.value for p in permissions]}"
            )

    return Depends(permission_checker)
