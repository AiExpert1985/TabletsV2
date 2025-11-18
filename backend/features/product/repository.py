"""
Product repository with company-aware data access.

Example implementation of CompanyAwareRepository pattern.
"""
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.base_repository import CompanyAwareRepository
from core.company_context import CompanyContext
from features.product.models import Product


class ProductRepository(CompanyAwareRepository[Product]):
    """
    Product repository with automatic company filtering.

    Inherits:
        - get_all_for_company()
        - get_by_id_for_company()
        - count_for_company()
        - ensure_company_ownership()
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize product repository."""
        super().__init__(db, Product)

    async def create(self, product: Product) -> Product:
        """
        Create a new product.

        Args:
            product: Product instance with company_id already set

        Returns:
            Created product
        """
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product) -> Product:
        """
        Update existing product.

        Args:
            product: Product instance to update

        Returns:
            Updated product
        """
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        """
        Delete a product.

        Args:
            product: Product instance to delete
        """
        await self.db.delete(product)
        await self.db.commit()

    async def get_by_sku(
        self,
        sku: str,
        company_ctx: CompanyContext
    ) -> Product | None:
        """
        Get product by SKU within user's company.

        Args:
            sku: Product SKU
            company_ctx: Company context for filtering

        Returns:
            Product or None
        """
        query = select(Product).where(Product.sku == sku)
        query = company_ctx.filter_query_by_company(query, Product)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_products(
        self,
        search_term: str,
        company_ctx: CompanyContext,
        skip: int = 0,
        limit: int = 100
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
        query = (
            select(Product)
            .where(Product.name.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
        )

        # CRITICAL: Apply company filtering
        query = company_ctx.filter_query_by_company(query, Product)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_low_stock_products(
        self,
        company_ctx: CompanyContext
    ) -> Sequence[Product]:
        """
        Get products below reorder level within user's company.

        Args:
            company_ctx: Company context for filtering

        Returns:
            List of low-stock products
        """
        query = (
            select(Product)
            .where(Product.stock_quantity <= Product.reorder_level)
            .where(Product.is_active == True)
        )

        # CRITICAL: Apply company filtering
        query = company_ctx.filter_query_by_company(query, Product)

        result = await self.db.execute(query)
        return result.scalars().all()
