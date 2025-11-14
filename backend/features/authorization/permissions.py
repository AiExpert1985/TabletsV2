"""
Permission system for granular CRUD-based access control.

Defines all permissions in the system organized by feature domain.
"""
import enum


class Permission(str, enum.Enum):
    """
    Granular permissions for all system operations.

    Organized by feature domain with CRUD operations:
    - view: Read access
    - create: Create new records
    - edit: Modify existing records
    - delete: Remove records
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


class CompanyRole(str, enum.Enum):
    """
    Company-level roles for organization-specific access control.

    These roles are scoped to a single company.
    """
    ADMIN = "admin"                    # Company administrator
    ACCOUNTANT = "accountant"          # Financial operations
    SALES_MANAGER = "sales_manager"    # Sales operations
    WAREHOUSE_KEEPER = "warehouse_keeper"  # Warehouse operations
    SALESPERSON = "salesperson"        # Limited sales access
    VIEWER = "viewer"                  # Read-only access


# System role is already defined in auth/models.py as UserRole.SYSTEM_ADMIN
# We'll use that for system-level operations


def get_all_permissions() -> list[Permission]:
    """Get list of all defined permissions."""
    return [p for p in Permission]


def get_permission_by_value(value: str) -> Permission | None:
    """
    Get Permission enum by string value.

    Args:
        value: Permission string (e.g., "users.view")

    Returns:
        Permission enum or None if not found
    """
    try:
        for p in Permission:
            if p.value == value:
                return p
        return None
    except Exception:
        return None
