"""Repository layer for audit logs - data access operations."""
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from features.audit_logs.models import AuditLog
from core.enums import EntityType


class AuditLogRepository:
    """Audit log repository implementation."""

    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save audit log to database."""
        self.db.add(audit_log)
        await self.db.flush()
        # Eagerly load user relationship
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.id == audit_log.id)
            .options(selectinload(AuditLog.user))
        )
        return result.scalar_one()

    async def get_all(
        self,
        company_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get all audit logs with optional company filtering.

        Args:
            company_id: Filter by company (None = system admin, sees all)
            skip: Number of records to skip
            limit: Maximum records to return
        """
        query = select(AuditLog).options(selectinload(AuditLog.user))

        # Apply company filter for non-system admins
        if company_id is not None:
            query = query.where(AuditLog.company_id == uuid.UUID(company_id))

        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_entity(
        self,
        entity_type: EntityType,
        entity_id: str,
        company_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific entity.

        Args:
            entity_type: Type of entity (User, Company, Product)
            entity_id: ID of the specific entity
            company_id: Filter by company (None = system admin, sees all)
            skip: Number of records to skip
            limit: Maximum records to return
        """
        conditions = [
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ]

        # Apply company filter for non-system admins
        if company_id is not None:
            conditions.append(AuditLog.company_id == uuid.UUID(company_id))

        query = (
            select(AuditLog)
            .where(and_(*conditions))
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_all(self, company_id: str | None = None) -> int:
        """
        Count total audit logs with optional company filtering.

        Args:
            company_id: Filter by company (None = system admin, sees all)
        """
        from sqlalchemy import func

        query = select(func.count(AuditLog.id))

        if company_id is not None:
            query = query.where(AuditLog.company_id == uuid.UUID(company_id))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_by_entity(
        self,
        entity_type: EntityType,
        entity_id: str,
        company_id: str | None = None
    ) -> int:
        """
        Count audit logs for a specific entity.

        Args:
            entity_type: Type of entity (User, Company, Product)
            entity_id: ID of the specific entity
            company_id: Filter by company (None = system admin, sees all)
        """
        from sqlalchemy import func

        conditions = [
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ]

        if company_id is not None:
            conditions.append(AuditLog.company_id == uuid.UUID(company_id))

        query = select(func.count(AuditLog.id)).where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0
