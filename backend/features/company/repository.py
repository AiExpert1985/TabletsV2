"""Repository layer for company feature."""
import uuid
from datetime import datetime, timezone
from typing import Protocol
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from features.company.models import Company


# ============================================================================
# Repository Interface (Protocol)
# ============================================================================

class ICompanyRepository(Protocol):
    """Interface for company repository."""

    async def create(self, name: str) -> Company: ...
    async def get_by_id(self, company_id: str) -> Company | None: ...
    async def get_by_name(self, name: str) -> Company | None: ...
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Company]: ...
    async def update(self, company_id: str, name: str | None = None, is_active: bool | None = None) -> Company | None: ...
    async def delete(self, company_id: str) -> bool: ...


# ============================================================================
# Repository Implementation
# ============================================================================

class CompanyRepository:
    """Company repository implementation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str) -> Company:
        """Create new company."""
        company = Company(name=name)
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def get_by_id(self, company_id: str) -> Company | None:
        """Get company by ID."""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Company | None:
        """Get company by name."""
        result = await self.db.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Company]:
        """Get all companies with pagination."""
        result = await self.db.execute(
            select(Company)
            .order_by(Company.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(
        self,
        company_id: str,
        name: str | None = None,
        is_active: bool | None = None
    ) -> Company | None:
        """Update company."""
        # Build update dict
        update_data = {"updated_at": datetime.now(timezone.utc)}
        if name is not None:
            update_data["name"] = name
        if is_active is not None:
            update_data["is_active"] = is_active

        # Update
        await self.db.execute(
            update(Company)
            .where(Company.id == company_id)
            .values(**update_data)
        )

        # Return updated company
        return await self.get_by_id(company_id)

    async def delete(self, company_id: str) -> bool:
        """Delete company (cascade deletes users)."""
        from sqlalchemy import delete as sql_delete
        result = await self.db.execute(
            sql_delete(Company).where(Company.id == company_id)
        )
        return result.rowcount > 0
