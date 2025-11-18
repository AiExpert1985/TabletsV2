"""FastAPI dependencies for users feature."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.features.auth.schemas import UserResponse
from core.dependencies import get_db
from features.auth.models import User
from features.users.repository import UserRepository
from features.auth.dependencies import CurrentUser
from features.users.service import UserService
from features.authorization.permission_checker import require_system_admin as check_system_admin


async def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserService:
    """Get user service."""
    user_repo = UserRepository(db)
    return UserService(user_repo)


async def require_system_admin(current_user: CurrentUser) -> None:
    """
    Require system admin role.

    Uses the new permission checker for consistency.

    Raises:
        PermissionDeniedException: User is not system admin
    """
    check_system_admin(current_user)


def build_user_response(user: User) -> "UserResponse":
    """
    Build UserResponse with calculated permissions.

    Args:
        user: User model

    Returns:
        UserResponse with permissions populated
    """
    from features.users.schemas import UserResponse
    from features.authorization.service import create_authorization_service

    # Calculate permissions for the user
    auth_service = create_authorization_service(user)
    permissions = auth_service.get_permission_list()

    return UserResponse(
        id=str(user.id),
        phone_number=user.phone_number,
        email=user.email,
        company_id=str(user.company_id) if user.company_id else None,
        role=user.role.value,
        company_roles=user.company_roles,
        permissions=permissions,
        is_active=user.is_active,
        is_phone_verified=user.is_phone_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
