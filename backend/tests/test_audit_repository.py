"""Integration tests for audit repository."""
import pytest
from uuid import uuid4
from features.audit.repository import AuditLogRepository
from features.audit.models import AuditLog
from features.users.models import User
from core.enums import AuditAction, EntityType


class TestAuditLogRepository:
    """Test AuditLogRepository with real database."""

    @pytest.mark.asyncio
    async def test_save_audit_log(self, audit_repo: AuditLogRepository, test_user: User):
        """Save audit log successfully."""
        # Arrange
        audit_log = AuditLog(
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            action=AuditAction.CREATE,
            changes='{"name": "Test"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )

        # Act
        result = await audit_repo.save(audit_log)

        # Assert
        assert result.id is not None
        assert result.entity_type == EntityType.USER
        assert result.action == AuditAction.CREATE
        assert result.username == test_user.name

    @pytest.mark.asyncio
    async def test_get_all_no_filter(
        self,
        audit_repo: AuditLogRepository,
        test_user: User,
        test_admin_user: User
    ):
        """Get all logs without company filter (system admin)."""
        # Arrange - Create logs for different companies
        log1 = AuditLog(
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            action=AuditAction.CREATE,
            changes='{"name": "User1"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )
        log2 = AuditLog(
            entity_type=EntityType.PRODUCT,
            entity_id=str(uuid4()),
            action=AuditAction.UPDATE,
            changes='{"price": {"old": 100, "new": 200}}',
            user_id=test_admin_user.id,
            username=test_admin_user.name,
            company_id=test_admin_user.company_id,
        )
        await audit_repo.save(log1)
        await audit_repo.save(log2)

        # Act
        result = await audit_repo.get_all(company_id=None, skip=0, limit=10)

        # Assert
        assert len(result) >= 2
        assert any(log.entity_type == EntityType.USER for log in result)
        assert any(log.entity_type == EntityType.PRODUCT for log in result)

    @pytest.mark.asyncio
    async def test_get_all_with_company_filter(
        self,
        audit_repo: AuditLogRepository,
        test_user: User,
        test_company
    ):
        """Get logs filtered by company."""
        # Arrange
        log = AuditLog(
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            action=AuditAction.CREATE,
            changes='{"name": "Test"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )
        await audit_repo.save(log)

        # Act
        result = await audit_repo.get_all(
            company_id=str(test_company.id),
            skip=0,
            limit=10
        )

        # Assert
        assert len(result) >= 1
        assert all(log.company_id == test_company.id for log in result)

    @pytest.mark.asyncio
    async def test_get_by_entity(
        self,
        audit_repo: AuditLogRepository,
        test_user: User
    ):
        """Get logs for specific entity."""
        # Arrange
        entity_id = str(uuid4())
        log1 = AuditLog(
            entity_type=EntityType.USER,
            entity_id=entity_id,
            action=AuditAction.CREATE,
            changes='{"name": "Created"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )
        log2 = AuditLog(
            entity_type=EntityType.USER,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            changes='{"name": {"old": "Created", "new": "Updated"}}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )
        log3 = AuditLog(  # Different entity
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            action=AuditAction.CREATE,
            changes='{"name": "Other"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=test_user.company_id,
        )
        await audit_repo.save(log1)
        await audit_repo.save(log2)
        await audit_repo.save(log3)

        # Act
        result = await audit_repo.get_by_entity(
            entity_type=EntityType.USER,
            entity_id=entity_id,
            company_id=None,  # System admin
            skip=0,
            limit=10
        )

        # Assert
        assert len(result) == 2
        assert all(log.entity_id == entity_id for log in result)
        assert result[0].action == AuditAction.UPDATE  # Most recent first
        assert result[1].action == AuditAction.CREATE

    @pytest.mark.asyncio
    async def test_count_all(
        self,
        audit_repo: AuditLogRepository,
        test_user: User
    ):
        """Count all logs."""
        # Arrange - Create multiple logs
        for i in range(3):
            log = AuditLog(
                entity_type=EntityType.PRODUCT,
                entity_id=str(uuid4()),
                action=AuditAction.CREATE,
                changes=f'{{"name": "Product{i}"}}',
                user_id=test_user.id,
                username=test_user.name,
                company_id=test_user.company_id,
            )
            await audit_repo.save(log)

        # Act
        count = await audit_repo.count_all(company_id=None)

        # Assert
        assert count >= 3

    @pytest.mark.asyncio
    async def test_count_by_entity(
        self,
        audit_repo: AuditLogRepository,
        test_user: User
    ):
        """Count logs for specific entity."""
        # Arrange
        entity_id = str(uuid4())
        for i in range(2):
            log = AuditLog(
                entity_type=EntityType.COMPANY,
                entity_id=entity_id,
                action=AuditAction.UPDATE,
                changes=f'{{"iteration": {i}}}',
                user_id=test_user.id,
                username=test_user.name,
                company_id=None,  # Company logs have no company_id
            )
            await audit_repo.save(log)

        # Create log for different entity
        other_log = AuditLog(
            entity_type=EntityType.COMPANY,
            entity_id=str(uuid4()),
            action=AuditAction.CREATE,
            changes='{"name": "Other"}',
            user_id=test_user.id,
            username=test_user.name,
            company_id=None,
        )
        await audit_repo.save(other_log)

        # Act
        count = await audit_repo.count_by_entity(
            entity_type=EntityType.COMPANY,
            entity_id=entity_id,
            company_id=None
        )

        # Assert
        assert count == 2

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        audit_repo: AuditLogRepository,
        test_user: User
    ):
        """Pagination works correctly."""
        # Arrange - Create 5 logs
        for i in range(5):
            log = AuditLog(
                entity_type=EntityType.USER,
                entity_id=str(uuid4()),
                action=AuditAction.CREATE,
                changes=f'{{"index": {i}}}',
                user_id=test_user.id,
                username=test_user.name,
                company_id=test_user.company_id,
            )
            await audit_repo.save(log)

        # Act - Get first 2
        page1 = await audit_repo.get_all(
            company_id=str(test_user.company_id),
            skip=0,
            limit=2
        )

        # Act - Get next 2
        page2 = await audit_repo.get_all(
            company_id=str(test_user.company_id),
            skip=2,
            limit=2
        )

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        # Should be different logs
        page1_ids = {log.id for log in page1}
        page2_ids = {log.id for log in page2}
        assert len(page1_ids & page2_ids) == 0  # No overlap
