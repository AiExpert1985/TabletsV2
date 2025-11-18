"""
Base repository with company-aware filtering support.

Provides reusable patterns for multi-tenant data access.
"""
from __future__ import annotations
from typing import TypeVar, Generic, Type, Sequence
from uuid import UUID
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from core.company_context import CompanyContext
from core.database import Base

# TypeVar for generic repository - bound to SQLAlchemy Base
ModelType = TypeVar("ModelType", bound=Base)


class CompanyAwareRepository(Generic[ModelType]):
    """
    Base repository with company filtering support.

    Provides common CRUD operations with automatic company isolation.

    Usage:
        class ProductRepository(CompanyAwareRepository[Product]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, Product)

            # Inherit get_all_for_company, get_by_id_for_company, etc.
            # Add custom methods as needed
    """

    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """
        Initialize repository.

        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def _build_base_query(self) -> Select:
        """Build base select query for the model."""
        return select(self.model)

    def _apply_company_filter(
        self,
        query: Select,
        company_ctx: CompanyContext
    ) -> Select:
        """
        Apply company filtering to query.

        Args:
            query: SQLAlchemy select query
            company_ctx: Company context

        Returns:
            Filtered query
        """
        return company_ctx.filter_query_by_company(query, self.model)

    async def get_all_for_company(
        self,
        company_ctx: CompanyContext,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ModelType]:
        """
        Get all records for the user's company (with pagination).

        System admin gets all records.
        Regular users get only their company's records.

        Args:
            company_ctx: Company context (determines filtering)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        query = self._build_base_query()
        query = self._apply_company_filter(query, company_ctx)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id_for_company(
        self,
        id: UUID,
        company_ctx: CompanyContext
    ) -> ModelType | None:
        """
        Get record by ID with company access check.

        Args:
            id: Record ID
            company_ctx: Company context

        Returns:
            Model instance or None

        Raises:
            HTTPException: 403 if trying to access another company's data
        """
        query = self._build_base_query().where(self.model.id == id)
        query = self._apply_company_filter(query, company_ctx)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_for_company(self, company_ctx: CompanyContext) -> int:
        """
        Count records for the user's company.

        Args:
            company_ctx: Company context

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)
        query = self._apply_company_filter(query, company_ctx)

        result = await self.db.execute(query)
        return result.scalar_one()

    def ensure_company_ownership(
        self,
        record: ModelType,
        company_ctx: CompanyContext
    ) -> None:
        """
        Verify record belongs to user's company.

        Args:
            record: Model instance to check
            company_ctx: Company context

        Raises:
            HTTPException: 403 if record belongs to different company
        """
        if hasattr(record, 'company_id'):
            company_ctx.ensure_company_access(record.company_id)
