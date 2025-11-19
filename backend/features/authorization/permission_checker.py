"""
Permission-based authorization checker.

Centralized permission checking utility with single-role system.
Supports company-aware authorization.

Usage:
    from features.authorization.permission_checker import require_permission

    # In route/service
    require_permission(current_user, Permission.CREATE_PRODUCTS)

    # With company check
    require_permission(current_user, Permission.CREATE_PRODUCTS, company_id=uuid)
"""
from uuid import UUID
from features.users.models import User
from core.enums import UserRole
from features.authorization.permissions import Permission
from features.authorization.role_permissions import get_permissions_for_role
from core.exceptions import PermissionDeniedException


def get_user_permissions(user: User) -> set[Permission]:
    """
    Get all permissions for a user based on their role.

    Args:
        user: Current user

    Returns:
        Set of all permissions the user has
    """
    # Simple: user has one role, role has permissions
    return get_permissions_for_role(user.role)


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user: Current user
        permission: Required permission

    Returns:
        True if user has the permission, False otherwise
    """
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def require_permission(
    user: User,
    permission: Permission,
    company_id: UUID | None = None,
) -> None:
    """
    Check if user has required permission and company access.

    This is the main authorization function to use in routes/services.
    Raises exception if user lacks permission or company access.

    Args:
        user: Current user
        permission: Required permission (e.g., Permission.CREATE_PRODUCTS)
        company_id: Optional company to check access for

    Raises:
        PermissionDeniedException: User lacks permission or company access

    Example:
        # Simple permission check
        require_permission(current_user, Permission.VIEW_USERS)

        # With company isolation
        require_permission(current_user, Permission.CREATE_PRODUCTS, product.company_id)
    """
    # 1. Check permission
    if not has_permission(user, permission):
        raise PermissionDeniedException(f"Missing required permission: {permission.value}")

    # 2. Check company isolation (if applicable)
    if company_id is not None:
        # System admin can access any company
        if user.role == UserRole.SYSTEM_ADMIN:
            return

        # Regular users must match company
        if user.company_id != company_id:
            raise PermissionDeniedException("Cannot access other company's data")


def require_any_permission(
    user: User,
    permissions: list[Permission],
    company_id: UUID | None = None,
) -> None:
    """
    Check if user has ANY of the required permissions.

    Useful for endpoints that accept multiple permission levels.

    Args:
        user: Current user
        permissions: List of acceptable permissions (OR logic)
        company_id: Optional company to check access for

    Raises:
        PermissionDeniedException: User lacks all permissions or company access

    Example:
        # Allow if user can either view or create products
        require_any_permission(
            current_user,
            [Permission.VIEW_PRODUCTS, Permission.CREATE_PRODUCTS]
        )
    """
    # Check if user has ANY of the permissions
    user_permissions = get_user_permissions(user)
    has_any = any(p in user_permissions for p in permissions)

    if not has_any:
        perm_values = [p.value for p in permissions]
        raise PermissionDeniedException(
            f"Missing required permissions. Need one of: {', '.join(perm_values)}"
        )

    # Check company isolation
    if company_id is not None:
        if user.role == UserRole.SYSTEM_ADMIN:
            return

        if user.company_id != company_id:
            raise PermissionDeniedException("Cannot access other company's data")


def require_all_permissions(
    user: User,
    permissions: list[Permission],
    company_id: UUID | None = None,
) -> None:
    """
    Check if user has ALL of the required permissions.

    Useful for complex operations requiring multiple permissions.

    Args:
        user: Current user
        permissions: List of required permissions (AND logic)
        company_id: Optional company to check access for

    Raises:
        PermissionDeniedException: User lacks any permission or company access
    """
    user_permissions = get_user_permissions(user)
    missing_permissions = [p for p in permissions if p not in user_permissions]

    if missing_permissions:
        perm_values = [p.value for p in missing_permissions]
        raise PermissionDeniedException(
            f"Missing required permissions: {', '.join(perm_values)}"
        )

    # Check company isolation
    if company_id is not None:
        if user.role == UserRole.SYSTEM_ADMIN:
            return

        if user.company_id != company_id:
            raise PermissionDeniedException("Cannot access other company's data")


def require_system_admin(user: User) -> None:
    """
    Require user to be a system administrator.

    Convenience function for system-admin-only endpoints.

    Args:
        user: Current user

    Raises:
        PermissionDeniedException: User is not system admin
    """
    if user.role != UserRole.SYSTEM_ADMIN:
        raise PermissionDeniedException("System administrator access required")


def require_company_admin(user: User) -> None:
    """
    Require user to be a company administrator (any type).

    Accepts both system admin and company admin roles.

    Args:
        user: Current user

    Raises:
        PermissionDeniedException: User is not an admin
    """
    if user.role not in [UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN]:
        raise PermissionDeniedException("Administrator access required")
