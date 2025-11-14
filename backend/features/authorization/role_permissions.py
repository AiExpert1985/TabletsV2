"""
Role-to-Permission mappings (Single Source of Truth).

This file defines what permissions each role has.
Uses PermissionGroups for type-safety and easier maintenance.
"""
from features.authorization.permissions import Permission, CompanyRole, PermissionGroups
from features.auth.models import UserRole


# ============================================================================
# Company Role Permission Mappings
# ============================================================================

COMPANY_ROLE_PERMISSIONS: dict[CompanyRole, set[Permission]] = {
    # Company Admin: Full access within company (but cannot create/delete users)
    CompanyRole.ADMIN: (
        PermissionGroups.USER_READ_ONLY  # View users only
        | {Permission.EDIT_USERS}  # Can edit but not create/delete
        | PermissionGroups.PRODUCT_MANAGEMENT
        | PermissionGroups.INVOICE_MANAGEMENT
        | PermissionGroups.PURCHASE_MANAGEMENT
        | PermissionGroups.WAREHOUSE_MANAGEMENT
        | PermissionGroups.FINANCIAL_REPORTING
        | {Permission.VIEW_AUDIT_LOGS}
    ),

    # Accountant: Financial operations and reports
    CompanyRole.ACCOUNTANT: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.PRODUCT_READ_ONLY
        | PermissionGroups.ACCOUNTING_PERMISSIONS  # Pre-defined accounting set
    ),

    # Sales Manager: Manage sales and invoices
    CompanyRole.SALES_MANAGER: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.SALES_PERMISSIONS  # Pre-defined sales set
    ),

    # Warehouse Keeper: Manage inventory and warehouse
    CompanyRole.WAREHOUSE_KEEPER: (
        PermissionGroups.WAREHOUSE_KEEPER_PERMISSIONS  # Pre-defined warehouse set
    ),

    # Salesperson: Create/view invoices only
    CompanyRole.SALESPERSON: (
        PermissionGroups.PRODUCT_READ_ONLY
        | {Permission.VIEW_INVOICES, Permission.CREATE_INVOICES}
        | PermissionGroups.WAREHOUSE_READ_ONLY  # Check stock
    ),

    # Viewer: Read-only access
    CompanyRole.VIEWER: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.PRODUCT_READ_ONLY
        | PermissionGroups.INVOICE_READ_ONLY
        | PermissionGroups.PURCHASE_READ_ONLY
        | PermissionGroups.WAREHOUSE_READ_ONLY
        | PermissionGroups.REPORTING_READ_ONLY
    ),
}


# ============================================================================
# System Role Permission Mappings
# ============================================================================

SYSTEM_ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    # System Admin: ALL permissions (including company management)
    UserRole.SYSTEM_ADMIN: PermissionGroups.ALL_PERMISSIONS,

    # Company Admin and User have no system-level permissions by default
    # They get permissions through their company roles
    UserRole.COMPANY_ADMIN: set(),
    UserRole.USER: set(),
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_permissions_for_company_role(role: CompanyRole) -> set[Permission]:
    """
    Get all permissions for a company role.

    Args:
        role: Company role enum

    Returns:
        Set of permissions for the role
    """
    return COMPANY_ROLE_PERMISSIONS.get(role, set())


def get_permissions_for_system_role(role: UserRole) -> set[Permission]:
    """
    Get all permissions for a system role.

    Args:
        role: System role enum (from UserRole)

    Returns:
        Set of permissions for the role
    """
    return SYSTEM_ROLE_PERMISSIONS.get(role, set())


def get_all_permissions_for_user(
    system_role: UserRole,
    company_roles: list[CompanyRole]
) -> set[Permission]:
    """
    Aggregate all permissions for a user based on their roles.

    Combines system role permissions + all company role permissions.

    Args:
        system_role: User's system role
        company_roles: List of user's company roles

    Returns:
        Set of all permissions (union of all roles)
    """
    # Start with system role permissions
    permissions = get_permissions_for_system_role(system_role).copy()

    # Add company role permissions
    for company_role in company_roles:
        permissions.update(get_permissions_for_company_role(company_role))

    return permissions
