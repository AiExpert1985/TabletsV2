"""Service layer for audit logs - business logic."""
import json
from typing import Any
from features.audit_logs.models import AuditLog
from features.audit_logs.repository import AuditLogRepository
from features.users.models import User
from core.enums import AuditAction, EntityType, UserRole


class AuditService:
    """
    Audit log service for tracking changes to business entities.

    Handles business logic: filtering sensitive data, formatting changes,
    multi-tenancy filtering.
    """

    # Fields to exclude from audit logs (sensitive data)
    SENSITIVE_FIELDS = {
        "hashed_password",
        "password_hash",
        "password",
        "token",
        "refresh_token",
        "secret",
        "api_key",
    }

    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    def _filter_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive fields from data."""
        return {
            key: value
            for key, value in data.items()
            if key.lower() not in self.SENSITIVE_FIELDS
        }

    def _format_changes_for_create(self, values: dict[str, Any]) -> str:
        """Format changes JSON for CREATE action."""
        filtered = self._filter_sensitive_data(values)
        return json.dumps(filtered, default=str)

    def _format_changes_for_update(
        self,
        old_values: dict[str, Any],
        new_values: dict[str, Any]
    ) -> str:
        """
        Format changes JSON for UPDATE action.

        Returns: {field: {old: val, new: val}} for changed fields only
        """
        old_filtered = self._filter_sensitive_data(old_values)
        new_filtered = self._filter_sensitive_data(new_values)

        changes = {}
        for key in new_filtered:
            if key in old_filtered and old_filtered[key] != new_filtered[key]:
                changes[key] = {
                    "old": old_filtered[key],
                    "new": new_filtered[key]
                }

        return json.dumps(changes, default=str)

    def _format_changes_for_delete(self, values: dict[str, Any]) -> str:
        """Format changes JSON for DELETE action."""
        filtered = self._filter_sensitive_data(values)
        return json.dumps(filtered, default=str)

    async def log_create(
        self,
        user: User,
        entity_type: EntityType,
        entity_id: str,
        values: dict[str, Any],
        company_id: str | None = None
    ) -> AuditLog:
        """
        Log entity creation.

        Args:
            user: User who created the entity
            entity_type: Type of entity (User, Company, Product)
            entity_id: ID of created entity
            values: New entity values
            company_id: Company ID for multi-tenancy (None for system admin)
        """
        changes = self._format_changes_for_create(values)

        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.CREATE,
            changes=changes,
            user_id=user.id,
            username=user.name,
            company_id=company_id
        )

        return await self.repository.save(audit_log)

    async def log_update(
        self,
        user: User,
        entity_type: EntityType,
        entity_id: str,
        old_values: dict[str, Any],
        new_values: dict[str, Any],
        company_id: str | None = None
    ) -> AuditLog:
        """
        Log entity update.

        Args:
            user: User who updated the entity
            entity_type: Type of entity (User, Company, Product)
            entity_id: ID of updated entity
            old_values: Original entity values
            new_values: Updated entity values
            company_id: Company ID for multi-tenancy (None for system admin)
        """
        changes = self._format_changes_for_update(old_values, new_values)

        # Only log if there are actual changes
        if changes == "{}":
            return None

        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=user.id,
            username=user.name,
            company_id=company_id
        )

        return await self.repository.save(audit_log)

    async def log_delete(
        self,
        user: User,
        entity_type: EntityType,
        entity_id: str,
        values: dict[str, Any],
        company_id: str | None = None
    ) -> AuditLog:
        """
        Log entity deletion.

        Args:
            user: User who deleted the entity
            entity_type: Type of entity (User, Company, Product)
            entity_id: ID of deleted entity
            values: Entity values before deletion
            company_id: Company ID for multi-tenancy (None for system admin)
        """
        changes = self._format_changes_for_delete(values)

        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.DELETE,
            changes=changes,
            user_id=user.id,
            username=user.name,
            company_id=company_id
        )

        return await self.repository.save(audit_log)

    async def get_all_logs(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get all audit logs with multi-tenancy filtering.

        System admin: sees all logs
        Company admin: sees only their company's logs
        """
        # System admin sees all
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return await self.repository.get_all(
                company_id=None,
                skip=skip,
                limit=limit
            )

        # Company users see only their company's logs
        company_id = str(current_user.company_id) if current_user.company_id else None
        return await self.repository.get_all(
            company_id=company_id,
            skip=skip,
            limit=limit
        )

    async def get_entity_logs(
        self,
        current_user: User,
        entity_type: EntityType,
        entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific entity with multi-tenancy filtering.

        System admin: sees all entity logs
        Company admin: sees only their company's entity logs
        """
        # System admin sees all
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return await self.repository.get_by_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                company_id=None,
                skip=skip,
                limit=limit
            )

        # Company users see only their company's logs
        company_id = str(current_user.company_id) if current_user.company_id else None
        return await self.repository.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            company_id=company_id,
            skip=skip,
            limit=limit
        )

    async def count_all_logs(self, current_user: User) -> int:
        """Count total audit logs with multi-tenancy filtering."""
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return await self.repository.count_all(company_id=None)

        company_id = str(current_user.company_id) if current_user.company_id else None
        return await self.repository.count_all(company_id=company_id)

    async def count_entity_logs(
        self,
        current_user: User,
        entity_type: EntityType,
        entity_id: str
    ) -> int:
        """Count audit logs for specific entity with multi-tenancy filtering."""
        if current_user.role == UserRole.SYSTEM_ADMIN:
            return await self.repository.count_by_entity(
                entity_type=entity_type,
                entity_id=entity_id,
                company_id=None
            )

        company_id = str(current_user.company_id) if current_user.company_id else None
        return await self.repository.count_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            company_id=company_id
        )
