"""Audit trail FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import get_db
from features.audit.repository import AuditRepository
from features.audit.service import AuditService


def get_audit_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuditRepository:
    """Get audit repository instance."""
    return AuditRepository(db)


def get_audit_service(
    repository: Annotated[AuditRepository, Depends(get_audit_repository)]
) -> AuditService:
    """Get audit service instance."""
    return AuditService(repository)
