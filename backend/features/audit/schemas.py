"""Pydantic schemas (DTOs) for audit logs API."""
from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    id: str
    entity_type: str
    entity_id: str
    action: str
    changes: str  # JSON string
    user_id: str | None
    username: str
    company_id: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs with pagination metadata."""

    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int
