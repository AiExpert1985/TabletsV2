"""Audit trail request/response schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""
    id: UUID
    timestamp: datetime
    user_id: UUID
    username: str
    user_role: str
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None
    changes: Optional[dict[str, Any]] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response schema for audit log list with pagination."""
    items: list[AuditLogResponse]
    total: int


class EntityHistoryResponse(BaseModel):
    """Response schema for entity history."""
    entity_type: str
    entity_id: str
    history: list[AuditLogResponse]


class AuditLogFilters(BaseModel):
    """Query parameters for filtering audit logs."""
    company_id: Optional[UUID] = Field(None, description="Filter by company")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    user_id: Optional[UUID] = Field(None, description="Filter by user")
    action: Optional[str] = Field(None, description="Filter by action (CREATE, UPDATE, DELETE)")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    limit: int = Field(100, ge=1, le=1000, description="Page size")
    offset: int = Field(0, ge=0, description="Page offset")
