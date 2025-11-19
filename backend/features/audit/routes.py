"""Audit logs routes - System Admin and Company Admin."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from features.audit.schemas import AuditLogResponse, AuditLogListResponse
from features.audit.service import AuditService
from features.audit.dependencies import get_audit_service
from features.auth.dependencies import CurrentUser
from features.authorization.permission_checker import require_permission
from features.authorization.permissions import Permission
from core.enums import EntityType


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=AuditLogListResponse)
async def get_all_audit_logs(
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """
    Get all audit logs with multi-tenancy filtering.

    - System admin: sees all logs across all companies
    - Company admin: sees only their company's logs

    Requires: VIEW_AUDIT_LOGS permission
    """
    # Check permission
    require_permission(current_user, Permission.VIEW_AUDIT_LOGS)

    # Get logs with multi-tenancy filtering (handled in service)
    logs = await audit_service.get_all_logs(
        current_user=current_user,
        skip=skip,
        limit=limit
    )
    total = await audit_service.count_all_logs(current_user)

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                entity_type=log.entity_type.value,
                entity_id=log.entity_id,
                action=log.action.value,
                changes=log.changes,
                user_id=str(log.user_id) if log.user_id else None,
                username=log.username,
                company_id=str(log.company_id) if log.company_id else None,
                timestamp=log.timestamp
            )
            for log in logs
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{entity_type}/{entity_id}", response_model=AuditLogListResponse)
async def get_entity_audit_logs(
    entity_type: EntityType,
    entity_id: str,
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """
    Get audit logs for a specific entity with multi-tenancy filtering.

    - System admin: sees all entity logs
    - Company admin: sees only their company's entity logs

    Requires: VIEW_AUDIT_LOGS permission
    """
    # Check permission
    require_permission(current_user, Permission.VIEW_AUDIT_LOGS)

    # Get entity logs with multi-tenancy filtering (handled in service)
    logs = await audit_service.get_entity_logs(
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )
    total = await audit_service.count_entity_logs(
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id
    )

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                entity_type=log.entity_type.value,
                entity_id=log.entity_id,
                action=log.action.value,
                changes=log.changes,
                user_id=str(log.user_id) if log.user_id else None,
                username=log.username,
                company_id=str(log.company_id) if log.company_id else None,
                timestamp=log.timestamp
            )
            for log in logs
        ],
        total=total,
        skip=skip,
        limit=limit
    )
