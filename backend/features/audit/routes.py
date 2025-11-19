"""Audit trail API routes."""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from features.audit.dependencies import get_audit_service
from features.audit.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    EntityHistoryResponse,
)
from features.audit.service import AuditService
from features.auth.dependencies import CurrentUser
from features.auth.models import User
from features.authorization.permission_checker import require_permission
from features.authorization.permissions import Permission

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    current_user: CurrentUser,
    service: Annotated[AuditService, Depends(get_audit_service)],
    company_id: Annotated[Optional[UUID], Query()] = None,
    entity_type: Annotated[Optional[str], Query()] = None,
    entity_id: Annotated[Optional[str], Query()] = None,
    user_id: Annotated[Optional[UUID], Query()] = None,
    action: Annotated[Optional[str], Query()] = None,
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditLogListResponse:
    """
    Get audit logs with filters (for global audit screen).

    Permissions:
    - Only system_admin and company_admin can access

    Access control:
    - system_admin: sees all logs
    - company_admin: sees only their company logs (automatically filtered)
    """
    # Check permission
    require_permission(current_user, Permission.VIEW_AUDIT_LOGS)

    # Get logs (service handles multi-tenancy filtering)
    logs, total = await service.get_audit_logs(
        current_user=current_user,
        company_id=company_id,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
    )


@router.get("/{entity_type}/{entity_id}", response_model=EntityHistoryResponse)
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    current_user: CurrentUser,
    service: Annotated[AuditService, Depends(get_audit_service)],
) -> EntityHistoryResponse:
    """
    Get audit history for a specific entity (for History button).

    Permissions:
    - Users can access if they can view that entity type
    - Multi-tenancy enforced (company users only see their company's entities)

    Args:
        entity_type: Type of entity (User, Product, Invoice, etc.)
        entity_id: ID of the entity
    """
    # Note: Permission check should be done based on entity type
    # For now, we allow access if user is authenticated
    # TODO: Add entity-specific permission checks based on entity_type

    # Get history (service handles multi-tenancy filtering)
    history = await service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        current_user=current_user,
    )

    return EntityHistoryResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        history=[AuditLogResponse.model_validate(log) for log in history],
    )
