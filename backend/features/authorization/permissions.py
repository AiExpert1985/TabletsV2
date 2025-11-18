"""
Permission system for granular CRUD-based access control.

Defines all permissions in the system organized by feature domain.
Uses type-safe enums and grouped constants to avoid string-based errors.
"""
import enum
from typing import Set


class Permission(str, enum.Enum):
    """
    Granular permissions for all system operations.

    Organized by feature domain with CRUD operations:
    - view: Read access
    - create: Create new records
    - edit: Modify existing records
    - delete: Remove records

    Usage:
        from features.authorization.permissions import Permission, PermissionGroups

        # Type-safe permission checking
        if auth_service.has_permission(Permission.VIEW_USERS):
            ...

        # Use permission groups
        if auth_service.has_any_permission(list(PermissionGroups.USER_MANAGEMENT)):
            ...
    """

    # ========================================================================
    # User Management
    # ========================================================================
    VIEW_USERS = "users.view"
    CREATE_USERS = "users.create"
    EDIT_USERS = "users.edit"
    DELETE_USERS = "users.delete"

    # ========================================================================
    # Company Management (System Admin only)
    # ========================================================================
    VIEW_COMPANIES = "companies.view"
    CREATE_COMPANIES = "companies.create"
    EDIT_COMPANIES = "companies.edit"
    DELETE_COMPANIES = "companies.delete"

    # ========================================================================
    # Products/Inventory
    # ========================================================================
    VIEW_PRODUCTS = "products.view"
    CREATE_PRODUCTS = "products.create"
    EDIT_PRODUCTS = "products.edit"
    DELETE_PRODUCTS = "products.delete"

    # ========================================================================
    # Sales/Invoices
    # ========================================================================
    VIEW_INVOICES = "invoices.view"
    CREATE_INVOICES = "invoices.create"
    EDIT_INVOICES = "invoices.edit"
    DELETE_INVOICES = "invoices.delete"

    # ========================================================================
    # Purchases
    # ========================================================================
    VIEW_PURCHASES = "purchases.view"
    CREATE_PURCHASES = "purchases.create"
    EDIT_PURCHASES = "purchases.edit"
    DELETE_PURCHASES = "purchases.delete"

    # ========================================================================
    # Warehouse Management
    # ========================================================================
    VIEW_WAREHOUSE = "warehouse.view"
    MANAGE_WAREHOUSE = "warehouse.manage"  # Full warehouse control

    # ========================================================================
    # Accounting/Reports
    # ========================================================================
    VIEW_REPORTS = "reports.view"
    EXPORT_REPORTS = "reports.export"
    VIEW_FINANCIALS = "financials.view"

    # ========================================================================
    # System Administration
    # ========================================================================
    VIEW_AUDIT_LOGS = "audit.view"
    VIEW_SYSTEM_SETTINGS = "settings.view"
    EDIT_SYSTEM_SETTINGS = "settings.edit"


# ============================================================================
# Permission Groups - Organized sets for easier management
# ============================================================================

class PermissionGroups:
    """
    Logical groupings of permissions by feature domain.

    Use these constants instead of manually listing permissions to:
    - Avoid typos and string errors
    - Maintain consistency across the codebase
    - Make code more readable and maintainable

    Example:
        # Instead of:
        permissions = ["users.view", "users.create", "users.edit", "users.delete"]

        # Use:
        permissions = PermissionGroups.USER_MANAGEMENT
    """

    # User Management
    USER_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
    }

    USER_READ_ONLY: Set[Permission] = {
        Permission.VIEW_USERS,
    }

    # Company Management (System Admin only)
    COMPANY_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_COMPANIES,
        Permission.CREATE_COMPANIES,
        Permission.EDIT_COMPANIES,
        Permission.DELETE_COMPANIES,
    }

    # Product/Inventory Management
    PRODUCT_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.EDIT_PRODUCTS,
        Permission.DELETE_PRODUCTS,
    }

    PRODUCT_READ_ONLY: Set[Permission] = {
        Permission.VIEW_PRODUCTS,
    }

    # Sales/Invoice Management
    INVOICE_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_INVOICES,
        Permission.CREATE_INVOICES,
        Permission.EDIT_INVOICES,
        Permission.DELETE_INVOICES,
    }

    INVOICE_READ_ONLY: Set[Permission] = {
        Permission.VIEW_INVOICES,
    }

    # Purchase Management
    PURCHASE_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_PURCHASES,
        Permission.CREATE_PURCHASES,
        Permission.EDIT_PURCHASES,
        Permission.DELETE_PURCHASES,
    }

    PURCHASE_READ_ONLY: Set[Permission] = {
        Permission.VIEW_PURCHASES,
    }

    # Warehouse Management
    WAREHOUSE_MANAGEMENT: Set[Permission] = {
        Permission.VIEW_WAREHOUSE,
        Permission.MANAGE_WAREHOUSE,
    }

    WAREHOUSE_READ_ONLY: Set[Permission] = {
        Permission.VIEW_WAREHOUSE,
    }

    # Financial/Reporting
    FINANCIAL_REPORTING: Set[Permission] = {
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_FINANCIALS,
    }

    REPORTING_READ_ONLY: Set[Permission] = {
        Permission.VIEW_REPORTS,
    }

    # System Administration
    SYSTEM_ADMIN_ONLY: Set[Permission] = {
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_SYSTEM_SETTINGS,
        Permission.EDIT_SYSTEM_SETTINGS,
    }

    # Common combinations
    ACCOUNTING_PERMISSIONS: Set[Permission] = (
        INVOICE_READ_ONLY
        | PURCHASE_READ_ONLY
        | FINANCIAL_REPORTING
    )

    SALES_PERMISSIONS: Set[Permission] = (
        PRODUCT_READ_ONLY
        | INVOICE_MANAGEMENT
        | REPORTING_READ_ONLY
    )

    WAREHOUSE_KEEPER_PERMISSIONS: Set[Permission] = (
        PRODUCT_MANAGEMENT
        | WAREHOUSE_MANAGEMENT
        | PURCHASE_READ_ONLY
    )

    # All permissions (for system admin)
    ALL_PERMISSIONS: Set[Permission] = {p for p in Permission}


# ============================================================================
# Helper Functions
# ============================================================================

def get_all_permissions() -> list[Permission]:
    """
    Get list of all defined permissions.

    Returns:
        List of all Permission enum values
    """
    return list(Permission)


def get_permission_by_value(value: str) -> Permission | None:
    """
    Get Permission enum by string value.

    Args:
        value: Permission string (e.g., "users.view")

    Returns:
        Permission enum or None if not found

    Example:
        perm = get_permission_by_value("users.view")
        if perm:
            print(perm == Permission.VIEW_USERS)  # True
    """
    try:
        for p in Permission:
            if p.value == value:
                return p
        return None
    except Exception:
        return None


def get_permissions_for_group(group_name: str) -> Set[Permission]:
    """
    Get permission set by group name.

    Args:
        group_name: Name of the permission group (e.g., "USER_MANAGEMENT")

    Returns:
        Set of permissions in that group, or empty set if not found

    Example:
        perms = get_permissions_for_group("USER_MANAGEMENT")
        # Returns {Permission.VIEW_USERS, Permission.CREATE_USERS, ...}
    """
    return getattr(PermissionGroups, group_name, set())
