"""
Role-to-Permission mappings (Single Source of Truth).

This file defines what permissions each role has.
Uses PermissionGroups for type-safety and easier maintenance.

Single role system - each user has ONE role that maps to a permission set.
"""
from features.authorization.permissions import Permission, PermissionGroups
from core.enums import UserRole


# ============================================================================
# Role Permission Mappings (Single Source of Truth)
# ============================================================================

ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    # System Admin: ALL permissions (including company management)
    UserRole.SYSTEM_ADMIN: PermissionGroups.ALL_PERMISSIONS,

    # Company Admin: Full access within company
    UserRole.COMPANY_ADMIN: (
        PermissionGroups.USER_MANAGEMENT  # Full user management
        | PermissionGroups.PRODUCT_MANAGEMENT
        | PermissionGroups.INVOICE_MANAGEMENT
        | PermissionGroups.PURCHASE_MANAGEMENT
        | PermissionGroups.WAREHOUSE_MANAGEMENT
        | PermissionGroups.FINANCIAL_REPORTING
        | {Permission.VIEW_AUDIT_LOGS}
    ),

    # Accountant: Financial operations and reports
    UserRole.ACCOUNTANT: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.PRODUCT_READ_ONLY
        | PermissionGroups.ACCOUNTING_PERMISSIONS
    ),

    # Sales Manager: Manage sales and invoices
    UserRole.SALES_MANAGER: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.SALES_PERMISSIONS
    ),

    # Warehouse Keeper: Manage inventory and warehouse
    UserRole.WAREHOUSE_KEEPER: (
        PermissionGroups.WAREHOUSE_KEEPER_PERMISSIONS
    ),

    # Salesperson: Create/view invoices only
    UserRole.SALESPERSON: (
        PermissionGroups.PRODUCT_READ_ONLY
        | {Permission.VIEW_INVOICES, Permission.CREATE_INVOICES}
        | PermissionGroups.WAREHOUSE_READ_ONLY
    ),

    # Viewer: Read-only access
    UserRole.VIEWER: (
        PermissionGroups.USER_READ_ONLY
        | PermissionGroups.PRODUCT_READ_ONLY
        | PermissionGroups.INVOICE_READ_ONLY
        | PermissionGroups.PURCHASE_READ_ONLY
        | PermissionGroups.WAREHOUSE_READ_ONLY
        | PermissionGroups.REPORTING_READ_ONLY
    ),
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_permissions_for_role(role: UserRole) -> set[Permission]:
    """
    Get all permissions for a user role.

    Args:
        role: User role enum

    Returns:
        Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, set())
