"""FastAPI dependencies for audit logs feature."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from features.audit_logs.repository import AuditLogRepository
from features.audit_logs.service import AuditService


async def get_audit_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AuditService:
    """Get audit service."""
    audit_repo = AuditLogRepository(db)
    return AuditService(audit_repo)
