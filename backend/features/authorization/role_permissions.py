"""
Role-to-Permission mappings (Single Source of Truth).

This file defines what permissions each role has.
Immutable configuration for authorization rules.
"""
from features.authorization.permissions import Permission, CompanyRole
from features.auth.models import UserRole


# ============================================================================
# Company Role Permission Mappings
# ============================================================================

COMPANY_ROLE_PERMISSIONS: dict[CompanyRole, set[Permission]] = {
    # Company Admin: Full access within company (but cannot create users)
    CompanyRole.ADMIN: {
        Permission.VIEW_USERS,
        Permission.EDIT_USERS,
        # NOTE: Cannot create/delete users (system admin only)

        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.EDIT_PRODUCTS,
        Permission.DELETE_PRODUCTS,

        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,
        Permission.EDIT_INVOICES,
        Permission.DELETE_INVOICES,

        Permission.VIEW_PURCHASES,
        Permission.CREATE_PURCHASES,
        Permission.EDIT_PURCHASES,
        Permission.DELETE_PURCHASES,

        Permission.VIEW_WAREHOUSE,
        Permission.MANAGE_WAREHOUSE,

        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_FINANCIALS,

        Permission.VIEW_AUDIT_LOGS,
    },

    # Accountant: Financial operations and reports
    CompanyRole.ACCOUNTANT: {
        Permission.VIEW_USERS,  # View users only

        Permission.VIEW_PRODUCTS,

        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,
        Permission.EDIT_INVOICES,

        Permission.VIEW_PURCHASES,
        Permission.CREATE_PURCHASES,
        Permission.EDIT_PURCHASES,

        Permission.VIEW_WAREHOUSE,  # View only

        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_FINANCIALS,
    },

    # Sales Manager: Manage sales and invoices
    CompanyRole.SALES_MANAGER: {
        Permission.VIEW_USERS,

        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.EDIT_PRODUCTS,

        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,
        Permission.EDIT_INVOICES,
        Permission.DELETE_INVOICES,

        Permission.VIEW_WAREHOUSE,

        Permission.VIEW_REPORTS,
    },

    # Warehouse Keeper: Manage inventory and warehouse
    CompanyRole.WAREHOUSE_KEEPER: {
        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.EDIT_PRODUCTS,

        Permission.VIEW_PURCHASES,

        Permission.VIEW_WAREHOUSE,
        Permission.MANAGE_WAREHOUSE,

        Permission.VIEW_REPORTS,  # Warehouse reports
    },

    # Salesperson: Create/view invoices only
    CompanyRole.SALESPERSON: {
        Permission.VIEW_PRODUCTS,

        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,

        Permission.VIEW_WAREHOUSE,  # Check stock
    },

    # Viewer: Read-only access
    CompanyRole.VIEWER: {
        Permission.VIEW_USERS,
        Permission.VIEW_PRODUCTS,
        Permission.VIEW_INVOICES,
        Permission.VIEW_PURCHASES,
        Permission.VIEW_WAREHOUSE,
        Permission.VIEW_REPORTS,
    },
}


# ============================================================================
# System Role Permission Mappings
# ============================================================================

SYSTEM_ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    # System Admin: ALL permissions (including company management)
    UserRole.SYSTEM_ADMIN: {
        # User management
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,  # Only system admin
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,  # Only system admin

        # Company management (system admin only)
        Permission.VIEW_COMPANIES,
        Permission.CREATE_COMPANIES,
        Permission.EDIT_COMPANIES,
        Permission.DELETE_COMPANIES,

        # All business operations
        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.EDIT_PRODUCTS,
        Permission.DELETE_PRODUCTS,

        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,
        Permission.EDIT_INVOICES,
        Permission.DELETE_INVOICES,

        Permission.VIEW_PURCHASES,
        Permission.CREATE_PURCHASES,
        Permission.EDIT_PURCHASES,
        Permission.DELETE_PURCHASES,

        Permission.VIEW_WAREHOUSE,
        Permission.MANAGE_WAREHOUSE,

        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_FINANCIALS,

        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_SYSTEM_SETTINGS,
        Permission.EDIT_SYSTEM_SETTINGS,
    },

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
