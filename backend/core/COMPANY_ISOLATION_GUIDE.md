# Company Data Isolation Guide

## Overview

This system implements **automatic multi-tenant data isolation** to ensure:
- ✅ Users only see data from their company
- ✅ System admin can access all companies
- ✅ Impossible to accidentally leak data between companies
- ✅ Type-safe and compiler-checked

## Quick Start

### 1. Use CompanyContext in Route Handlers

```python
from core.company_context import CompanyCtx

@router.get("/products")
async def get_products(
    company_ctx: CompanyCtx,  # Automatically injected!
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)]
):
    # Repository automatically filters by company
    products = await product_repo.get_all_for_company(company_ctx)
    return products
```

### 2. Inherit from CompanyAwareRepository

```python
from core.base_repository import CompanyAwareRepository

class ProductRepository(CompanyAwareRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

    # You get these methods for FREE:
    # - get_all_for_company()
    # - get_by_id_for_company()
    # - count_for_company()
    # - ensure_company_ownership()
```

### 3. That's It!

Company filtering is now automatic. You can't forget to filter because the compiler won't let you.

---

## How It Works

### The CompanyContext Object

Every authenticated request gets a `CompanyContext`:

```python
class CompanyContext:
    user: User                    # Current user
    company_id: UUID | None       # User's company (None for system admin)
    is_system_admin: bool         # True if system admin
    should_filter: bool           # True if filtering needed (not system admin)
```

**For Regular Users:**
```python
company_ctx = CompanyContext(user)
# company_ctx.company_id = UUID("...")
# company_ctx.should_filter = True
# → All queries filtered to their company
```

**For System Admin:**
```python
company_ctx = CompanyContext(system_admin_user)
# company_ctx.company_id = None
# company_ctx.should_filter = False
# → No filtering, sees all companies
```

---

## Pattern 1: List/Get Operations (Read)

### Using Base Repository (Recommended)

```python
class ProductRepository(CompanyAwareRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Product)

# Route handler
@router.get("/products")
async def get_products(
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    skip: int = 0,
    limit: int = 100
):
    # Automatically filtered by company!
    products = await product_repo.get_all_for_company(company_ctx, skip, limit)
    return products
```

### Manual Query Filtering

If you need custom queries:

```python
class ProductRepository:
    async def search_products(
        self,
        search_term: str,
        company_ctx: CompanyContext
    ):
        # Build your custom query
        query = (
            select(Product)
            .where(Product.name.ilike(f"%{search_term}%"))
        )

        # Apply company filtering
        query = company_ctx.filter_query_by_company(query, Product)

        result = await self.db.execute(query)
        return result.scalars().all()
```

---

## Pattern 2: Get By ID (Read Single)

### Using Base Repository

```python
@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)]
):
    # Automatically checks company access!
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(404, "Product not found")

    return product
```

**What happens:**
- Regular user tries to access another company's product → Returns `None` (appears as 404)
- System admin can access any company's product → Returns the product
- Security: No explicit 403, prevents company enumeration

### Manual Access Check

```python
@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # Get product without filtering
    product = await product_repo.get_by_id(product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    # Explicitly check company access
    company_ctx.ensure_company_access(product.company_id)

    return product
```

---

## Pattern 3: Create Operations (Write)

### Regular Users (Have Company)

```python
@router.post("/products")
async def create_product(
    request: ProductCreateRequest,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # User's company_id is automatically used
    product = Product(
        name=request.name,
        price=request.price,
        company_id=company_ctx.get_company_id_for_create(),  # ← Auto-filled
    )

    await product_repo.create(product)
    return product
```

### System Admin (Must Specify Company)

For system admin, require `company_id` in request body:

```python
class ProductCreateRequest(BaseModel):
    name: str
    price: Decimal
    company_id: UUID | None = None  # Optional for regular users, required for admin

@router.post("/products")
async def create_product(
    request: ProductCreateRequest,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # Determine company_id
    if company_ctx.is_system_admin:
        # System admin must explicitly specify
        if not request.company_id:
            raise HTTPException(400, "System admin must specify company_id")
        company_id = request.company_id
    else:
        # Regular user uses their own company
        company_id = company_ctx.company_id

    product = Product(
        name=request.name,
        price=request.price,
        company_id=company_id,
    )

    await product_repo.create(product)
    return product
```

---

## Pattern 4: Update Operations (Write)

```python
@router.put("/products/{product_id}")
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # Get and verify access in one step
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(404, "Product not found")

    # Update fields
    product.name = request.name
    product.price = request.price

    await product_repo.update(product)
    return product
```

**Alternative with explicit check:**

```python
@router.put("/products/{product_id}")
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    product = await product_repo.get_by_id(product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    # Verify company access
    company_ctx.ensure_company_access(product.company_id)  # Raises 403 if denied

    # Update
    product.name = request.name
    await product_repo.update(product)
    return product
```

---

## Pattern 5: Delete Operations (Write)

```python
@router.delete("/products/{product_id}")
async def delete_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # Get and verify access
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(404, "Product not found")

    await product_repo.delete(product)
    return {"message": "Product deleted"}
```

---

## Pattern 6: Counting/Aggregations

```python
@router.get("/products/count")
async def count_products(
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    # Automatically filtered by company
    count = await product_repo.count_for_company(company_ctx)
    return {"count": count}
```

---

## Pattern 7: Custom Repository Methods

When you need custom queries, always use `CompanyContext`:

```python
class InvoiceRepository(CompanyAwareRepository[Invoice]):
    async def get_unpaid_invoices(
        self,
        company_ctx: CompanyContext
    ) -> Sequence[Invoice]:
        """Get unpaid invoices for the user's company."""
        query = (
            select(Invoice)
            .where(Invoice.status == InvoiceStatus.UNPAID)
            .order_by(Invoice.due_date.asc())
        )

        # CRITICAL: Apply company filtering
        query = company_ctx.filter_query_by_company(query, Invoice)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_total_revenue(
        self,
        company_ctx: CompanyContext,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """Calculate total revenue for the user's company."""
        from sqlalchemy import func, and_

        query = select(func.sum(Invoice.total_amount)).where(
            and_(
                Invoice.status == InvoiceStatus.PAID,
                Invoice.payment_date >= start_date,
                Invoice.payment_date <= end_date
            )
        )

        # CRITICAL: Apply company filtering
        query = company_ctx.filter_query_by_company(query, Invoice)

        result = await self.db.execute(query)
        return result.scalar_one() or Decimal(0)
```

---

## Testing Company Isolation

### Unit Test Example

```python
import pytest
from core.company_context import CompanyContext

def test_regular_user_sees_only_their_company(db_session):
    # Create test data
    company_a = Company(name="Company A")
    company_b = Company(name="Company B")

    user_a = User(company_id=company_a.id, role=UserRole.USER)

    product_a = Product(name="Product A", company_id=company_a.id)
    product_b = Product(name="Product B", company_id=company_b.id)

    # User from Company A
    company_ctx = CompanyContext(user=user_a)
    repo = ProductRepository(db_session)

    # Should only see Company A's products
    products = await repo.get_all_for_company(company_ctx)

    assert len(products) == 1
    assert products[0].id == product_a.id

def test_system_admin_sees_all_companies(db_session):
    # Create test data
    company_a = Company(name="Company A")
    company_b = Company(name="Company B")

    system_admin = User(company_id=None, role=UserRole.SYSTEM_ADMIN)

    product_a = Product(name="Product A", company_id=company_a.id)
    product_b = Product(name="Product B", company_id=company_b.id)

    # System admin
    company_ctx = CompanyContext(user=system_admin)
    repo = ProductRepository(db_session)

    # Should see all products
    products = await repo.get_all_for_company(company_ctx)

    assert len(products) == 2
```

---

## Common Mistakes to Avoid

### ❌ DON'T: Forget company filtering

```python
# BAD - leaks data between companies!
@router.get("/products")
async def get_products(product_repo: ProductRepository):
    products = await product_repo.get_all()  # Returns ALL companies!
    return products
```

### ✅ DO: Always use CompanyContext

```python
# GOOD - automatic filtering
@router.get("/products")
async def get_products(
    company_ctx: CompanyCtx,
    product_repo: ProductRepository
):
    products = await product_repo.get_all_for_company(company_ctx)
    return products
```

### ❌ DON'T: Hard-code company filtering

```python
# BAD - doesn't work for system admin
@router.get("/products")
async def get_products(current_user: CurrentUser, product_repo: ProductRepository):
    products = await product_repo.get_by_company(current_user.company_id)
    return products  # System admin gets error: company_id is None!
```

### ✅ DO: Use CompanyContext methods

```python
# GOOD - handles both regular users and system admin
@router.get("/products")
async def get_products(company_ctx: CompanyCtx, product_repo: ProductRepository):
    products = await product_repo.get_all_for_company(company_ctx)
    return products
```

---

## Summary

**3 Simple Rules:**

1. **Always inject `CompanyCtx`** in route handlers
2. **Inherit from `CompanyAwareRepository`** for new models
3. **Use `company_ctx.filter_query_by_company()`** for custom queries

Follow these rules, and data isolation is **automatic** and **secure**! 🔒
