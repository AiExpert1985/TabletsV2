"""Audit trail service for business logic."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from features.audit.models import AuditAction, AuditLog
from features.audit.repository import AuditRepository
from features.auth.models import User


# Sensitive fields to exclude from audit logs
SENSITIVE_FIELDS = {
    'password',
    'hashed_password',
    'password_hash',
    'token',
    'secret',
    'api_key',
    'access_token',
    'refresh_token',
}


class AuditService:
    """Service for audit trail operations."""

    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def _sanitize_values(self, values: dict[str, Any]) -> dict[str, Any]:
        """
        Remove sensitive fields from values.

        Args:
            values: Dictionary of field values

        Returns:
            Sanitized dictionary with sensitive fields removed
        """
        return {
            k: v for k, v in values.items()
            if k.lower() not in SENSITIVE_FIELDS
        }

    def _compute_changes(
        self,
        old_values: dict[str, Any],
        new_values: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """
        Compute field-level changes between old and new values.

        Args:
            old_values: Original values
            new_values: Updated values

        Returns:
            Dictionary of changes: {field: {old: x, new: y}}
        """
        changes = {}

        # Check all fields in new_values
        for key, new_val in new_values.items():
            old_val = old_values.get(key)
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val,
                }

        # Check for removed fields (in old but not in new)
        for key in old_values:
            if key not in new_values:
                changes[key] = {
                    "old": old_values[key],
                    "new": None,
                }

        return changes

    async def log_create(
        self,
        user: User,
        entity_type: str,
        entity_id: str,
        values: dict[str, Any],
        company_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """
        Log entity creation.

        Args:
            user: User who performed the action
            entity_type: Type of entity (User, Product, etc.)
            entity_id: ID of created entity
            values: New entity values
            company_id: Company context
            description: Optional description

        Returns:
            Created audit log
        """
        sanitized_values = self._sanitize_values(values)

        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user.id,
            username=user.phone_number,
            user_role=user.role,
            company_id=company_id,
            company_name=user.company.name if user.company else None,
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=None,
            new_values=sanitized_values,
            changes=None,
            description=description,
        )

        return await self.repository.create(audit_log)

    async def log_update(
        self,
        user: User,
        entity_type: str,
        entity_id: str,
        old_values: dict[str, Any],
        new_values: dict[str, Any],
        company_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """
        Log entity update.

        Args:
            user: User who performed the action
            entity_type: Type of entity
            entity_id: ID of updated entity
            old_values: Original values
            new_values: Updated values
            company_id: Company context
            description: Optional description

        Returns:
            Created audit log
        """
        sanitized_old = self._sanitize_values(old_values)
        sanitized_new = self._sanitize_values(new_values)
        changes = self._compute_changes(sanitized_old, sanitized_new)

        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user.id,
            username=user.phone_number,
            user_role=user.role,
            company_id=company_id,
            company_name=user.company.name if user.company else None,
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=sanitized_old,
            new_values=sanitized_new,
            changes=changes,
            description=description,
        )

        return await self.repository.create(audit_log)

    async def log_delete(
        self,
        user: User,
        entity_type: str,
        entity_id: str,
        old_values: dict[str, Any],
        company_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """
        Log entity deletion.

        Args:
            user: User who performed the action
            entity_type: Type of entity
            entity_id: ID of deleted entity
            old_values: Values before deletion
            company_id: Company context
            description: Optional description

        Returns:
            Created audit log
        """
        sanitized_values = self._sanitize_values(old_values)

        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user.id,
            username=user.phone_number,
            user_role=user.role,
            company_id=company_id,
            company_name=user.company.name if user.company else None,
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=sanitized_values,
            new_values=None,
            changes=None,
            description=description,
        )

        return await self.repository.create(audit_log)

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        current_user: User,
    ) -> list[AuditLog]:
        """
        Get audit history for a specific entity.

        Access control:
        - Company users only see their company's entities
        - System admin sees all

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            current_user: User requesting history

        Returns:
            List of audit logs for the entity
        """
        # Get history from repository
        history = await self.repository.get_entity_history(entity_type, entity_id)

        # Apply multi-tenancy filter for non-system admins
        if current_user.company_id is not None:
            # Filter to only logs from user's company
            history = [
                log for log in history
                if log.company_id == current_user.company_id
            ]

        return history

    async def get_audit_logs(
        self,
        current_user: User,
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
        Get audit logs with filters (for global audit screen).

        Access control:
        - system_admin: sees all logs
        - company_admin: sees only their company logs
        - others: should not call this (enforced by permissions)

        Args:
            current_user: User requesting logs
            company_id: Filter by company
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_id: Filter by user
            action: Filter by action
            start_date: Filter start date
            end_date: Filter end date
            limit: Page size
            offset: Page offset

        Returns:
            Tuple of (audit logs, total count)
        """
        # Apply company filter for non-system admins
        if current_user.company_id is not None:
            # Company admin: force filter to their company
            company_id = current_user.company_id

        return await self.repository.get_logs(
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
