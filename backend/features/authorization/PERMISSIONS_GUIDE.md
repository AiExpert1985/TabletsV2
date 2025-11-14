# Permission System Usage Guide

## Overview

The permission system is **100% type-safe** - no strings needed! Use enums and permission groups to avoid errors.

## Quick Start

### ✅ Type-Safe (Recommended)

```python
from features.authorization.permissions import Permission, PermissionGroups
from features.authorization.dependencies import require_permission

# Single permission
@router.get("/users")
async def get_users(
    _: Annotated[None, Depends(require_permission(Permission.VIEW_USERS))]
):
    ...

# Multiple permissions (any)
from features.authorization.dependencies import require_any_permission

@router.get("/dashboard")
async def dashboard(
    _: Annotated[None, Depends(require_any_permission(
        Permission.VIEW_REPORTS,
        Permission.VIEW_FINANCIALS
    ))]
):
    ...

# Permission groups
if auth_service.has_all_permissions(list(PermissionGroups.USER_MANAGEMENT)):
    # User has view, create, edit, delete for users
    ...
```

### ❌ Don't Use Strings

```python
# BAD - error-prone!
if auth_service.has_permission("users.view"):  # Typo risk!
    ...

# GOOD - type-safe!
if auth_service.has_permission(Permission.VIEW_USERS):  # Autocomplete!
    ...
```

## Available Permission Groups

### By Resource

- `PermissionGroups.USER_MANAGEMENT` - All user CRUD permissions
- `PermissionGroups.COMPANY_MANAGEMENT` - All company CRUD permissions
- `PermissionGroups.PRODUCT_MANAGEMENT` - All product CRUD permissions
- `PermissionGroups.INVOICE_MANAGEMENT` - All invoice CRUD permissions
- `PermissionGroups.PURCHASE_MANAGEMENT` - All purchase CRUD permissions
- `PermissionGroups.WAREHOUSE_MANAGEMENT` - Warehouse + manage permissions
- `PermissionGroups.FINANCIAL_REPORTING` - Reports + financials

### Read-Only Variants

- `PermissionGroups.USER_READ_ONLY` - View users only
- `PermissionGroups.PRODUCT_READ_ONLY` - View products only
- `PermissionGroups.INVOICE_READ_ONLY` - View invoices only
- `PermissionGroups.PURCHASE_READ_ONLY` - View purchases only
- `PermissionGroups.WAREHOUSE_READ_ONLY` - View warehouse only
- `PermissionGroups.REPORTING_READ_ONLY` - View reports only

### Role-Based Combinations

- `PermissionGroups.ACCOUNTING_PERMISSIONS` - Invoice + Purchase + Financial
- `PermissionGroups.SALES_PERMISSIONS` - Product (view) + Invoice (full) + Reports
- `PermissionGroups.WAREHOUSE_KEEPER_PERMISSIONS` - Product + Warehouse + Purchase (view)
- `PermissionGroups.ALL_PERMISSIONS` - Everything (system admin)

## Common Patterns

### Route Protection

```python
from features.authorization.permissions import Permission
from features.authorization.dependencies import require_permission

@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    _: Annotated[None, Depends(require_permission(Permission.CREATE_PRODUCTS))]
):
    # Only users with CREATE_PRODUCTS permission can access
    ...
```

### In-Code Permission Checks

```python
from features.authorization.permissions import Permission, PermissionGroups

# Single permission
if auth_service.has_permission(Permission.EDIT_USERS):
    # Allow editing
    ...

# Any of multiple
if auth_service.has_any_permission([
    Permission.VIEW_FINANCIALS,
    Permission.VIEW_REPORTS
]):
    # Show financial dashboard
    ...

# All of multiple
if auth_service.has_all_permissions(list(PermissionGroups.INVOICE_MANAGEMENT)):
    # Full invoice management access
    ...
```

### Adding New Permissions

1. Add to `Permission` enum in `features/authorization/permissions.py`:
   ```python
   class Permission(str, enum.Enum):
       ...
       # New feature
       VIEW_ANALYTICS = "analytics.view"
       EXPORT_ANALYTICS = "analytics.export"
   ```

2. Create permission group (optional):
   ```python
   class PermissionGroups:
       ...
       ANALYTICS: Set[Permission] = {
           Permission.VIEW_ANALYTICS,
           Permission.EXPORT_ANALYTICS,
       }
   ```

3. Assign to roles in `role_permissions.py`:
   ```python
   CompanyRole.ADMIN: (
       ...
       | PermissionGroups.ANALYTICS
   )
   ```

4. Use in routes:
   ```python
   @router.get("/analytics")
   async def get_analytics(
       _: Annotated[None, Depends(require_permission(Permission.VIEW_ANALYTICS))]
   ):
       ...
   ```

## All 28 Permissions

```python
# User Management
Permission.VIEW_USERS
Permission.CREATE_USERS       # System admin only
Permission.EDIT_USERS
Permission.DELETE_USERS       # System admin only

# Company Management (System admin only)
Permission.VIEW_COMPANIES
Permission.CREATE_COMPANIES
Permission.EDIT_COMPANIES
Permission.DELETE_COMPANIES

# Products
Permission.VIEW_PRODUCTS
Permission.CREATE_PRODUCTS
Permission.EDIT_PRODUCTS
Permission.DELETE_PRODUCTS

# Invoices
Permission.VIEW_INVOICES
Permission.CREATE_INVOICES
Permission.EDIT_INVOICES
Permission.DELETE_INVOICES

# Purchases
Permission.VIEW_PURCHASES
Permission.CREATE_PURCHASES
Permission.EDIT_PURCHASES
Permission.DELETE_PURCHASES

# Warehouse
Permission.VIEW_WAREHOUSE
Permission.MANAGE_WAREHOUSE

# Reporting
Permission.VIEW_REPORTS
Permission.EXPORT_REPORTS
Permission.VIEW_FINANCIALS

# System
Permission.VIEW_AUDIT_LOGS
Permission.VIEW_SYSTEM_SETTINGS
Permission.EDIT_SYSTEM_SETTINGS
```

## Benefits of This Approach

✅ **Type Safety** - IDE autocomplete, compile-time errors
✅ **No Typos** - Can't misspell permission names
✅ **Centralized** - One place to see all permissions
✅ **Grouped** - Logical organization by feature
✅ **Maintainable** - Change once, applies everywhere
✅ **Discoverable** - Easy to find available permissions
