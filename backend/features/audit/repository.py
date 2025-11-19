"""Audit trail repository for data access."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.audit.models import AuditLog


class AuditRepository:
    """Repository for audit log data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[AuditLog]:
        """
        Get all audit logs for a specific entity.

        Args:
            entity_type: Type of entity (User, Product, etc.)
            entity_id: ID of the entity

        Returns:
            List of audit logs ordered by timestamp descending
        """
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id,
                )
            )
            .order_by(desc(AuditLog.timestamp))
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs(
        self,
        company_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        Get audit logs with filters and pagination.

        Args:
            company_id: Filter by company
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_id: Filter by user
            action: Filter by action
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Page size
            offset: Page offset

        Returns:
            Tuple of (audit logs, total count)
        """
        # Build filter conditions
        conditions = []

        if company_id is not None:
            conditions.append(AuditLog.company_id == company_id)

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)

        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)

        if user_id:
            conditions.append(AuditLog.user_id == user_id)

        if action:
            conditions.append(AuditLog.action == action)

        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)

        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)

        # Build base query
        where_clause = and_(*conditions) if conditions else None

        # Get total count
        count_query = select(func.count(AuditLog.id))
        if where_clause is not None:
            count_query = count_query.where(where_clause)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = select(AuditLog)
        if where_clause is not None:
            query = query.where(where_clause)

        query = (
            query
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total
