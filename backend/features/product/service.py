"""Business logic for product management."""
from decimal import Decimal
from typing import Sequence
from uuid import UUID
from features.product.models import Product
from features.product.repository import ProductRepository
from core.company_context import CompanyContext
from core.exceptions import AppException


class ProductAlreadyExistsException(AppException):
    """Product SKU already exists in company."""

    def __init__(self, sku: str) -> None:
        super().__init__(
            code="PRODUCT_ALREADY_EXISTS",
            message=f"Product with SKU '{sku}' already exists"
        )


class ProductNotFoundException(AppException):
    """Product not found or not accessible."""

    def __init__(self) -> None:
        super().__init__(
            code="PRODUCT_NOT_FOUND",
            message="Product not found"
        )


class ProductService:
    """Product management service - handles business logic for product operations."""

    product_repo: ProductRepository

    def __init__(self, product_repo: ProductRepository) -> None:
        self.product_repo = product_repo

    async def create_product(
        self,
        company_ctx: CompanyContext,
        name: str,
        sku: str,
        selling_price: Decimal,
        description: str | None = None,
        cost_price: Decimal | None = None,
        stock_quantity: int = 0,
        reorder_level: int = 10,
        company_id: UUID | None = None,
    ) -> Product:
        """
        Create a new product.

        Business rules:
        - System admin must specify company_id
        - Regular users use their own company_id (ignoring passed company_id)
        - SKU must be unique within company
        - Selling price is required
        - Cost price defaults to 0.00

        Args:
            company_ctx: Company context for filtering
            name: Product name
            sku: Product SKU (unique within company)
            selling_price: Selling price
            description: Product description (optional)
            cost_price: Cost price (defaults to 0.00)
            stock_quantity: Initial stock (defaults to 0)
            reorder_level: Reorder threshold (defaults to 10)
            company_id: Company UUID (required for system admin, ignored for regular users)

        Returns:
            Created product

        Raises:
            ProductAlreadyExistsException: SKU already exists in company
            ValueError: System admin didn't specify company_id
        """
        # 1. Determine company_id based on user type
        if company_ctx.is_system_admin:
            if not company_id:
                raise ValueError("System admin must specify company_id when creating products")
            target_company_id = company_id
        else:
            # Regular user - use their company, ignore passed company_id
            target_company_id = company_ctx.company_id

        # 2. Check for duplicate SKU within company
        existing = await self.product_repo.get_by_sku(sku, company_ctx)
        if existing:
            raise ProductAlreadyExistsException(sku)

        # 3. Create product
        product = Product(
            company_id=target_company_id,
            name=name,
            sku=sku,
            description=description,
            cost_price=cost_price or Decimal("0.00"),
            selling_price=selling_price,
            stock_quantity=stock_quantity,
            reorder_level=reorder_level,
        )

        # 4. Save to repository
        product = await self.product_repo.create(product)

        return product

    async def get_product(
        self,
        product_id: UUID,
        company_ctx: CompanyContext,
    ) -> Product:
        """
        Get product by ID with company access control.

        Args:
            product_id: Product UUID
            company_ctx: Company context for filtering

        Returns:
            Product

        Raises:
            ProductNotFoundException: Product not found or not accessible
        """
        product = await self.product_repo.get_by_id_for_company(product_id, company_ctx)
        if not product:
            raise ProductNotFoundException()
        return product

    async def list_products(
        self,
        company_ctx: CompanyContext,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Get all products for user's company.

        Args:
            company_ctx: Company context for filtering
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of products
        """
        return await self.product_repo.get_all_for_company(company_ctx, skip, limit)

    async def search_products(
        self,
        search_term: str,
        company_ctx: CompanyContext,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Search products by name within user's company.

        Args:
            search_term: Search string
            company_ctx: Company context for filtering
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of matching products
        """
        return await self.product_repo.search_products(search_term, company_ctx, skip, limit)

    async def get_low_stock_products(
        self,
        company_ctx: CompanyContext,
    ) -> Sequence[Product]:
        """
        Get products below reorder level.

        Args:
            company_ctx: Company context for filtering

        Returns:
            List of low-stock products
        """
        return await self.product_repo.get_low_stock_products(company_ctx)

    async def update_product(
        self,
        product_id: UUID,
        company_ctx: CompanyContext,
        name: str | None = None,
        sku: str | None = None,
        description: str | None = None,
        cost_price: Decimal | None = None,
        selling_price: Decimal | None = None,
        stock_quantity: int | None = None,
        reorder_level: int | None = None,
        is_active: bool | None = None,
    ) -> Product:
        """
        Update existing product.

        Business rules:
        - Can only update products in user's company
        - SKU must be unique within company if changed

        Args:
            product_id: Product UUID
            company_ctx: Company context for filtering
            name: New name (optional)
            sku: New SKU (optional)
            description: New description (optional)
            cost_price: New cost price (optional)
            selling_price: New selling price (optional)
            stock_quantity: New stock quantity (optional)
            reorder_level: New reorder level (optional)
            is_active: New active status (optional)

        Returns:
            Updated product

        Raises:
            ProductNotFoundException: Product not found or not accessible
            ProductAlreadyExistsException: New SKU already exists
        """
        # 1. Get product with company access check
        product = await self.get_product(product_id, company_ctx)

        # 2. Check SKU uniqueness if changing
        if sku and sku != product.sku:
            existing = await self.product_repo.get_by_sku(sku, company_ctx)
            if existing:
                raise ProductAlreadyExistsException(sku)

        # 3. Update fields (only if provided)
        if name is not None:
            product.name = name
        if sku is not None:
            product.sku = sku
        if description is not None:
            product.description = description
        if cost_price is not None:
            product.cost_price = cost_price
        if selling_price is not None:
            product.selling_price = selling_price
        if stock_quantity is not None:
            product.stock_quantity = stock_quantity
        if reorder_level is not None:
            product.reorder_level = reorder_level
        if is_active is not None:
            product.is_active = is_active

        # 4. Save changes
        product = await self.product_repo.update(product)

        return product

    async def delete_product(
        self,
        product_id: UUID,
        company_ctx: CompanyContext,
    ) -> None:
        """
        Delete a product.

        Args:
            product_id: Product UUID
            company_ctx: Company context for filtering

        Raises:
            ProductNotFoundException: Product not found or not accessible
        """
        # Get product with company access check
        product = await self.get_product(product_id, company_ctx)

        # Delete
        await self.product_repo.delete(product)
