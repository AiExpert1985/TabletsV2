"""Shared enums used across features."""
import enum


class UserRole(str, enum.Enum):
    """
    User roles in the system.

    Single role per user - maps directly to permission sets.
    """
    # System-level role
    SYSTEM_ADMIN = "system_admin"  # Full access, manages companies

    # Company-level roles
    COMPANY_ADMIN = "company_admin"      # Full access within company
    ACCOUNTANT = "accountant"            # Financial operations & reports
    SALES_MANAGER = "sales_manager"      # Manage sales & salespeople
    WAREHOUSE_KEEPER = "warehouse_keeper"  # Inventory & warehouse operations
    SALESPERSON = "salesperson"          # Create invoices, view products
    VIEWER = "viewer"                    # Read-only access


class AuditAction(str, enum.Enum):
    """Actions tracked in audit logs."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class EntityType(str, enum.Enum):
    """Entity types tracked in audit logs."""
    USER = "User"
    COMPANY = "Company"
    PRODUCT = "Product"
