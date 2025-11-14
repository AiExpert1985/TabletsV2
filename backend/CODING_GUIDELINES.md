# Backend Coding Guidelines

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Multi-Tenancy & Company Isolation](#multi-tenancy--company-isolation)
3. [Authentication & Authorization](#authentication--authorization)
4. [Repository Pattern](#repository-pattern)
5. [API Endpoint Patterns](#api-endpoint-patterns)
6. [Database Models](#database-models)
7. [Error Handling](#error-handling)
8. [Logging](#logging)
9. [Type Safety & Validation](#type-safety--validation)
10. [Testing](#testing)
11. [Code Style & Conventions](#code-style--conventions)

---

## Project Architecture

### Directory Structure

```
backend/
├── core/                          # Core infrastructure
│   ├── config.py                 # Application settings
│   ├── database.py               # Database connection & session
│   ├── exceptions.py             # Custom exception classes
│   ├── company_context.py        # Multi-tenant isolation logic
│   └── base_repository.py        # Base repository class
│
├── features/                      # Feature modules (domain-driven)
│   ├── auth/                     # Authentication feature
│   │   ├── models.py            # User, RefreshToken models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── repository.py        # Data access layer
│   │   ├── service.py           # Business logic
│   │   ├── routes.py            # API endpoints
│   │   └── dependencies.py      # FastAPI dependencies
│   │
│   ├── authorization/            # Authorization feature
│   │   ├── permissions.py       # Permission definitions
│   │   ├── role_permissions.py  # Role-to-permission mapping
│   │   └── dependencies.py      # Permission checking dependencies
│   │
│   ├── company/                  # Company management
│   ├── product/                  # Product/inventory management
│   └── logging/                  # Logging infrastructure
│
└── main.py                        # Application entry point
```

### Feature Module Pattern

Each feature follows a consistent structure:

```
feature_name/
├── models.py       # SQLAlchemy models (database tables)
├── schemas.py      # Pydantic schemas (API contracts)
├── repository.py   # Data access layer (queries)
├── service.py      # Business logic (optional, for complex features)
├── routes.py       # API endpoints (route handlers)
└── dependencies.py # FastAPI dependencies (optional)
```

**Rules:**
- ✅ Models define database structure only (no business logic)
- ✅ Schemas define API contracts and validation
- ✅ Repositories handle all database queries
- ✅ Routes handle HTTP concerns (request/response)
- ✅ Services contain complex business logic (optional)
- ❌ Never put business logic in models or routes

---

## Multi-Tenancy & Company Isolation

**CRITICAL:** All business data MUST be isolated by company.

### Pattern Overview

```python
from core.company_context import CompanyCtx
from core.base_repository import CompanyAwareRepository

# 1. Repository inherits from CompanyAwareRepository
class ProductRepository(CompanyAwareRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

# 2. Route handler injects CompanyCtx
@router.get("/products")
async def get_products(
    company_ctx: CompanyCtx,  # Automatically injected!
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)]
):
    # 3. Use repository methods that automatically filter by company
    products = await product_repo.get_all_for_company(company_ctx)
    return products
```

### Mandatory Rules

1. **All business models MUST have `company_id` field:**
   ```python
   company_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       ForeignKey("companies.id", ondelete="CASCADE"),
       nullable=False,
       index=True  # ALWAYS index for performance
   )
   ```

2. **All repositories MUST inherit from `CompanyAwareRepository`:**
   ```python
   class MyRepository(CompanyAwareRepository[MyModel]):
       def __init__(self, db: AsyncSession):
           super().__init__(db, MyModel)
   ```

3. **All route handlers MUST inject `CompanyCtx`:**
   ```python
   async def my_endpoint(company_ctx: CompanyCtx, ...):
   ```

4. **Custom queries MUST use `company_ctx.filter_query_by_company()`:**
   ```python
   query = select(Product).where(Product.name.ilike(f"%{search}%"))
   query = company_ctx.filter_query_by_company(query, Product)  # CRITICAL!
   ```

5. **System admin handling:**
   - Regular users: Automatically filtered to their company
   - System admin: No filtering, sees all companies
   - This is handled automatically by `CompanyContext.should_filter`

### Reference Documentation

See [`core/COMPANY_ISOLATION_GUIDE.md`](core/COMPANY_ISOLATION_GUIDE.md) for detailed examples of all patterns.

---

## Authentication & Authorization

### Authentication Pattern

**JWT tokens with refresh tokens:**

```python
# Login returns both tokens
{
    "access_token": "eyJ...",      # Short-lived (15 minutes)
    "refresh_token": "eyJ...",     # Long-lived (7 days)
    "token_type": "bearer"
}
```

**Getting current user:**

```python
from features.auth.dependencies import CurrentUser

@router.get("/me")
async def get_current_user(current_user: CurrentUser):
    return current_user
```

### Authorization Pattern

**Type-safe permissions using `PermissionGroups`:**

```python
from features.authorization.permissions import Permission, PermissionGroups
from features.authorization.dependencies import require_permission

# Single permission
@router.post("/products")
async def create_product(
    _: Annotated[None, Depends(require_permission(Permission.CREATE_PRODUCTS))],
    ...
):
    pass

# Multiple permissions (any)
@router.get("/dashboard")
async def get_dashboard(
    _: Annotated[None, Depends(require_permission(
        Permission.VIEW_PRODUCTS,
        Permission.VIEW_INVOICES
    ))],
    ...
):
    pass
```

### Permission Rules

1. **Always use `Permission` enum, never strings:**
   ```python
   # ✅ GOOD
   require_permission(Permission.VIEW_PRODUCTS)

   # ❌ BAD
   require_permission("view_products")
   ```

2. **Use `PermissionGroups` for role definitions:**
   ```python
   # In role_permissions.py
   CompanyRole.ACCOUNTANT: (
       PermissionGroups.ACCOUNTING_PERMISSIONS
       | PermissionGroups.USER_READ_ONLY
   )
   ```

3. **Default deny:** Users have no permissions unless explicitly granted

4. **Permission naming convention:** `{ACTION}_{RESOURCE}` (e.g., `VIEW_PRODUCTS`, `CREATE_INVOICES`)

### Reference Documentation

See [`features/authorization/PERMISSIONS_GUIDE.md`](features/authorization/PERMISSIONS_GUIDE.md) for detailed usage.

---

## Repository Pattern

### Base Repository

All repositories MUST inherit from `CompanyAwareRepository`:

```python
from core.base_repository import CompanyAwareRepository
from sqlalchemy.ext.asyncio import AsyncSession

class ProductRepository(CompanyAwareRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    # You get these methods for FREE:
    # - get_all_for_company(company_ctx, skip, limit)
    # - get_by_id_for_company(id, company_ctx)
    # - count_for_company(company_ctx)
    # - ensure_company_ownership(record, company_ctx)
```

### Custom Repository Methods

```python
class ProductRepository(CompanyAwareRepository[Product]):
    async def search_by_name(
        self,
        search_term: str,
        company_ctx: CompanyContext,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Product]:
        """Search products by name within user's company."""
        query = (
            select(Product)
            .where(Product.name.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
        )

        # CRITICAL: Always apply company filtering
        query = company_ctx.filter_query_by_company(query, Product)

        result = await self.db.execute(query)
        return result.scalars().all()
```

### Repository Rules

1. **All database queries go through repositories** (never in routes or services)
2. **All custom methods MUST accept `CompanyContext`** as a parameter
3. **All queries MUST apply company filtering** (except for auth/system operations)
4. **Use type hints for all parameters and return types**
5. **Use descriptive method names** (`get_by_sku`, not `get_product`)

### Repository Dependency

```python
# In repository.py
async def get_product_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProductRepository:
    """Dependency to get product repository."""
    return ProductRepository(db)

# In routes.py
@router.get("/products")
async def get_products(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)]
):
    pass
```

---

## API Endpoint Patterns

### CRUD Endpoints

```python
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Annotated
from core.company_context import CompanyCtx
from features.authorization.dependencies import require_permission

router = APIRouter(prefix="/api/products", tags=["products"])

# LIST (with pagination and filtering)
@router.get("", response_model=list[ProductResponse])
async def get_products(
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """Get all products for the user's company."""
    products = await product_repo.get_all_for_company(company_ctx, skip, limit)
    return [ProductResponse.model_validate(p) for p in products]

# GET BY ID
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))]
):
    """Get a single product by ID."""
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return ProductResponse.model_validate(product)

# CREATE
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.CREATE_PRODUCTS))]
):
    """Create a new product."""
    # Determine company_id
    if company_ctx.is_system_admin:
        if not request.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System admin must specify company_id"
            )
        company_id = request.company_id
    else:
        company_id = company_ctx.company_id

    # Create product
    product = Product(
        company_id=company_id,
        name=request.name,
        sku=request.sku,
        cost_price=request.cost_price,
        selling_price=request.selling_price,
        stock_quantity=request.stock_quantity
    )

    product = await product_repo.create(product)
    return ProductResponse.model_validate(product)

# UPDATE
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.UPDATE_PRODUCTS))]
):
    """Update a product."""
    # Get and verify access
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Update fields (only provided fields)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    product = await product_repo.update(product)
    return ProductResponse.model_validate(product)

# DELETE
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.DELETE_PRODUCTS))]
):
    """Delete a product."""
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await product_repo.delete(product)
```

### Endpoint Rules

1. **Always use type hints** for all parameters and return types
2. **Always specify `response_model`** for GET/POST/PUT endpoints
3. **Always use `HTTPException` for errors** (not raising generic exceptions)
4. **Return 404 for not found**, not 403 (prevents company enumeration)
5. **Use `Query()` for query parameters** with validation and description
6. **Use `status.HTTP_*` constants** for status codes
7. **Always inject `CompanyCtx`** for business endpoints
8. **Always check permissions** using `require_permission()`
9. **Use descriptive docstrings** for all endpoints

### Pagination

```python
@router.get("")
async def get_items(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    items = await repo.get_all_for_company(company_ctx, skip, limit)
    return items
```

---

## Database Models

### Model Pattern

```python
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from features.auth.models import UUID

class Product(Base):
    """
    Product/Inventory item.

    Demonstrates company-isolated data model.
    """
    __tablename__ = "products"

    # Primary key (UUID)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Company isolation (CRITICAL for multi-tenancy)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # IMPORTANT: Index for fast filtering
    )

    # Business fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Numeric fields (use Decimal for money)
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    # Booleans
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps (always with timezone)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product {self.name} (company={self.company_id})>"
```

### Model Rules

1. **Always use `uuid.UUID` for primary keys** (not auto-increment integers)
2. **Always include `company_id`** with foreign key and CASCADE delete
3. **Always index `company_id`** for performance
4. **Use `Decimal` for monetary values**, never `float`
5. **Use `DateTime(timezone=True)`** for all timestamps
6. **Use `timezone.utc`** for timestamp defaults
7. **Include `created_at` and `updated_at`** on all models
8. **Use `Mapped[type]`** for type safety
9. **Use descriptive docstrings** for models and complex fields
10. **Add `__repr__`** for debugging

### Field Type Guidelines

```python
# Strings
name: Mapped[str] = mapped_column(String(255), nullable=False)

# Optional strings
description: Mapped[str | None] = mapped_column(String(1000))

# Integers
quantity: Mapped[int] = mapped_column(default=0)

# Decimals (for money)
price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

# Booleans
is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# UUIDs
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

# Enums
from enum import Enum as PyEnum
from sqlalchemy import Enum

class Status(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

status: Mapped[Status] = mapped_column(
    Enum(Status, native_enum=False),
    default=Status.ACTIVE
)
```

---

## Error Handling

### Exception Hierarchy

```python
# core/exceptions.py
class AppException(Exception):
    """Base application exception."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

# Usage in routes
from fastapi import HTTPException, status

# Not found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# Bad request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid input data"
)

# Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission to access this resource"
)

# Unauthorized
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"}
)
```

### Error Response Format

```json
{
    "detail": "Error message here"
}
```

For validation errors (422):

```json
{
    "detail": [
        {
            "loc": ["body", "price"],
            "msg": "ensure this value is greater than 0",
            "type": "value_error.number.not_gt"
        }
    ]
}
```

### Error Handling Rules

1. **Use `HTTPException` for HTTP errors**
2. **Use specific status codes** (`status.HTTP_*` constants)
3. **Return 404 instead of 403** when accessing another company's data (prevents enumeration)
4. **Log errors appropriately** (warnings for expected errors, errors for unexpected)
5. **Never expose internal details** in error messages
6. **Use descriptive error messages** that help users understand what went wrong

---

## Logging

### Logger Setup

```python
from features.logging.logger import get_logger

logger = get_logger(__name__)  # Use module name
```

### Logging Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"User {user_id} attempting to access product {product_id}")

# INFO: General informational messages
logger.info(f"User {user.email} logged in successfully")

# WARNING: Something unexpected but recoverable
logger.warning(
    f"User {user.id} (company={company_id}) attempted to access "
    f"resource from company={resource_company_id}"
)

# ERROR: Serious problem that needs attention
logger.error(
    f"Failed to send email to {email}: {str(e)}",
    exc_info=True  # Include traceback
)
```

### Logging Rules

1. **Use structured logging** with context
2. **Never log sensitive data** (passwords, tokens, personal info)
3. **Log authentication/authorization failures** (warnings)
4. **Log unexpected errors** with stack traces (`exc_info=True`)
5. **Use appropriate log levels**
6. **Include relevant context** (user_id, company_id, resource_id)

---

## Type Safety & Validation

### Pydantic Schemas

```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from uuid import UUID

class ProductCreateRequest(BaseModel):
    """Request to create a new product."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Product name"
    )

    sku: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Stock keeping unit"
    )

    cost_price: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Cost price"
    )

    selling_price: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Selling price"
    )

    stock_quantity: int = Field(
        default=0,
        ge=0,
        description="Current stock quantity"
    )

    company_id: UUID | None = Field(
        default=None,
        description="Company ID (system admin only)"
    )

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU format."""
        if not v.isalnum():
            raise ValueError("SKU must be alphanumeric")
        return v.upper()

    @field_validator("selling_price")
    @classmethod
    def validate_selling_price(cls, v: Decimal, info) -> Decimal:
        """Ensure selling price is greater than cost price."""
        cost_price = info.data.get("cost_price")
        if cost_price and v < cost_price:
            raise ValueError("Selling price must be greater than cost price")
        return v

class ProductUpdateRequest(BaseModel):
    """Request to update a product (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    sku: str | None = Field(None, min_length=1, max_length=100)
    cost_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    selling_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    stock_quantity: int | None = Field(None, ge=0)
    is_active: bool | None = None

class ProductResponse(BaseModel):
    """Product response."""

    id: str
    company_id: str
    name: str
    sku: str
    cost_price: Decimal
    selling_price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

### Validation Rules

1. **Use Pydantic for all request/response schemas**
2. **Use `Field()` for constraints and descriptions**
3. **Use `field_validator` for complex validation**
4. **Create separate schemas for create/update/response**
5. **Make update schemas fully optional** (partial updates)
6. **Use `from_attributes = True` for response schemas** (ORM mode)
7. **Convert UUIDs to strings in responses** (JSON compatibility)

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Pytest fixtures
├── test_auth.py         # Auth feature tests
├── test_products.py     # Product feature tests
└── test_company_isolation.py  # Multi-tenancy tests
```

### Test Patterns

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.models import User, UserRole
from features.company.models import Company
from features.product.models import Product

@pytest.mark.asyncio
async def test_get_products_filters_by_company(
    client: AsyncClient,
    db_session: AsyncSession,
    company_a: Company,
    company_b: Company,
    user_a: User  # User from company A
):
    """Test that users only see products from their company."""

    # Create products for both companies
    product_a = Product(
        company_id=company_a.id,
        name="Product A",
        sku="SKU-A",
        cost_price=Decimal("10.00"),
        selling_price=Decimal("20.00")
    )
    product_b = Product(
        company_id=company_b.id,
        name="Product B",
        sku="SKU-B",
        cost_price=Decimal("15.00"),
        selling_price=Decimal("30.00")
    )
    db_session.add_all([product_a, product_b])
    await db_session.commit()

    # Login as user from company A
    response = await client.post("/api/auth/login", json={
        "email": user_a.email,
        "password": "password123"
    })
    token = response.json()["access_token"]

    # Get products
    response = await client.get(
        "/api/products",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    products = response.json()

    # Should only see product A
    assert len(products) == 1
    assert products[0]["id"] == str(product_a.id)
```

### Testing Rules

1. **Write tests for all CRUD operations**
2. **Test company isolation thoroughly**
3. **Test permission checks**
4. **Test validation errors**
5. **Use fixtures for common setup**
6. **Use descriptive test names** (`test_<what>_<when>_<expected>`)
7. **Test both success and failure cases**
8. **Test edge cases** (empty results, duplicates, invalid input)

---

## Code Style & Conventions

### Naming Conventions

```python
# Classes: PascalCase
class ProductRepository:
    pass

# Functions/methods: snake_case
def get_all_products():
    pass

# Variables: snake_case
product_count = 10

# Constants: UPPER_SNAKE_CASE
MAX_PRODUCTS = 1000

# Private attributes/methods: _leading_underscore
def _internal_helper():
    pass

# Enums: PascalCase class, UPPER_CASE values
class UserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    COMPANY_ADMIN = "company_admin"
```

### Import Organization

```python
# 1. Standard library imports
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Sequence

# 2. Third-party imports
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy import String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, Field

# 3. Local imports
from core.database import Base, get_db
from core.company_context import CompanyCtx
from features.auth.models import UUID
from features.authorization.dependencies import require_permission
```

### Docstrings

```python
def get_products(
    company_ctx: CompanyContext,
    skip: int = 0,
    limit: int = 100
) -> Sequence[Product]:
    """
    Get all products for the user's company.

    Args:
        company_ctx: Company context (determines filtering)
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of products

    Raises:
        HTTPException: 403 if access denied
    """
    pass
```

### General Rules

1. **Use type hints everywhere** (parameters, return types, variables)
2. **Use `Annotated` for dependency injection**
3. **Use `|` for union types** (not `Union` or `Optional`)
4. **Use descriptive variable names** (avoid abbreviations)
5. **Keep functions short** (< 50 lines ideally)
6. **One responsibility per function**
7. **Use early returns** to reduce nesting
8. **Add comments for complex logic**, not obvious code
9. **Follow PEP 8** (use linter like `ruff` or `black`)

---

## Quick Reference

### Checklist for New Features

When adding a new business feature (e.g., invoices, customers):

- [ ] Create model with `company_id` (indexed, foreign key, CASCADE)
- [ ] Create Pydantic schemas (create, update, response)
- [ ] Create repository inheriting from `CompanyAwareRepository`
- [ ] Create routes with permission checks
- [ ] All routes inject `CompanyCtx`
- [ ] All queries use company filtering
- [ ] Register router in `main.py`
- [ ] Import model in `main.py` for SQLAlchemy
- [ ] Add permissions to `Permission` enum
- [ ] Add permissions to `PermissionGroups`
- [ ] Update role permissions in `role_permissions.py`
- [ ] Write tests for CRUD operations
- [ ] Test company isolation
- [ ] Test permission checks

### Common Patterns

**Get all items:**
```python
items = await repo.get_all_for_company(company_ctx, skip, limit)
```

**Get by ID:**
```python
item = await repo.get_by_id_for_company(id, company_ctx)
if not item:
    raise HTTPException(404, "Not found")
```

**Create item:**
```python
company_id = (
    request.company_id
    if company_ctx.is_system_admin
    else company_ctx.company_id
)
item = Model(company_id=company_id, ...)
```

**Update item:**
```python
item = await repo.get_by_id_for_company(id, company_ctx)
if not item:
    raise HTTPException(404, "Not found")

update_data = request.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(item, field, value)
```

---

## Additional Resources

- [Company Isolation Guide](core/COMPANY_ISOLATION_GUIDE.md)
- [Permissions Usage Guide](features/authorization/PERMISSIONS_GUIDE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Last Updated:** 2025-11-14

**Maintained By:** Development Team
