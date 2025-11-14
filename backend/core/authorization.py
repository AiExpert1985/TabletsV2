"""Authorization helpers for role-based access control."""
from fastapi import HTTPException, status
from features.auth.models import User, UserRole


def require_system_admin(user: User) -> None:
    """
    Require user to be system_admin.

    Raises HTTPException 403 if user is not system_admin.
    """
    if user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can perform this action"
        )


def require_company_admin_or_system_admin(user: User) -> None:
    """
    Require user to be at least company_admin.

    Raises HTTPException 403 if user is regular user.
    """
    if user.role not in [UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


def check_company_access(user: User, company_id: str) -> None:
    """
    Check if user has access to a specific company.

    - System admin: Access to all companies
    - Other users: Access only to their own company

    Raises HTTPException 403 if user doesn't have access.
    """
    if user.role == UserRole.SYSTEM_ADMIN:
        return  # System admin has access to everything

    if user.company_id is None or str(user.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this company's data"
        )


def get_company_filter(user: User) -> str | None:
    """
    Get company_id filter for queries based on user role.

    Returns:
        - None: if system_admin (no filter, see all companies)
        - company_id: if company user (filter to user's company only)
    """
    if user.role == UserRole.SYSTEM_ADMIN:
        return None  # No filter for system admin
    return str(user.company_id) if user.company_id else None
