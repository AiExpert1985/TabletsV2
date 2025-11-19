"""Tests for audit service."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from features.audit.service import AuditService
from features.audit.models import AuditLog
from features.audit.repository import AuditLogRepository
from features.users.models import User
from core.enums import AuditAction, EntityType, UserRole


@pytest.fixture
def mock_audit_repo():
    """Mock audit repository."""
    repo = Mock(spec=AuditLogRepository)
    repo.save = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_by_entity = AsyncMock()
    repo.count_all = AsyncMock()
    repo.count_by_entity = AsyncMock()
    return repo


@pytest.fixture
def audit_service(mock_audit_repo):
    """Create audit service with mocked repository."""
    return AuditService(mock_audit_repo)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.name = "John Doe"
    user.company_id = uuid4()
    user.role = UserRole.SYSTEM_ADMIN
    return user


class TestAuditService:
    """Test AuditService."""

    @pytest.mark.asyncio
    async def test_log_create_success(self, audit_service, mock_audit_repo, mock_user):
        """Log create succeeds and filters sensitive data."""
        # Arrange
        values = {
            "name": "New Product",
            "price": 100,
            "password": "secret123",  # Should be filtered
            "hashed_password": "hash",  # Should be filtered
        }
        mock_log = Mock(spec=AuditLog)
        mock_audit_repo.save.return_value = mock_log

        # Act
        result = await audit_service.log_create(
            user=mock_user,
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            values=values,
            company_id=str(mock_user.company_id),
        )

        # Assert
        assert result == mock_log
        assert mock_audit_repo.save.called
        saved_log = mock_audit_repo.save.call_args[0][0]
        assert saved_log.action == AuditAction.CREATE
        assert saved_log.entity_type == EntityType.USER
        assert saved_log.user_id == mock_user.id
        assert saved_log.username == mock_user.name

        # Check sensitive data filtered
        import json
        changes = json.loads(saved_log.changes)
        assert "password" not in changes
        assert "hashed_password" not in changes
        assert changes["name"] == "New Product"
        assert changes["price"] == 100

    @pytest.mark.asyncio
    async def test_log_update_success(self, audit_service, mock_audit_repo, mock_user):
        """Log update captures old and new values."""
        # Arrange
        old_values = {"name": "Old Name", "price": 100}
        new_values = {"name": "New Name", "price": 200}
        mock_log = Mock(spec=AuditLog)
        mock_audit_repo.save.return_value = mock_log

        # Act
        result = await audit_service.log_update(
            user=mock_user,
            entity_type=EntityType.PRODUCT,
            entity_id=str(uuid4()),
            old_values=old_values,
            new_values=new_values,
            company_id=str(mock_user.company_id),
        )

        # Assert
        assert result == mock_log
        assert mock_audit_repo.save.called
        saved_log = mock_audit_repo.save.call_args[0][0]
        assert saved_log.action == AuditAction.UPDATE
        assert saved_log.username == mock_user.name

        # Check changes format
        import json
        changes = json.loads(saved_log.changes)
        assert changes["name"]["old"] == "Old Name"
        assert changes["name"]["new"] == "New Name"
        assert changes["price"]["old"] == 100
        assert changes["price"]["new"] == 200

    @pytest.mark.asyncio
    async def test_log_update_no_changes(self, audit_service, mock_audit_repo, mock_user):
        """Log update returns None when no changes."""
        # Arrange
        same_values = {"name": "Same", "price": 100}

        # Act
        result = await audit_service.log_update(
            user=mock_user,
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            old_values=same_values,
            new_values=same_values,
            company_id=None,
        )

        # Assert
        assert result is None
        assert not mock_audit_repo.save.called

    @pytest.mark.asyncio
    async def test_log_delete_success(self, audit_service, mock_audit_repo, mock_user):
        """Log delete succeeds."""
        # Arrange
        values = {"name": "Deleted Item", "status": "active"}
        mock_log = Mock(spec=AuditLog)
        mock_audit_repo.save.return_value = mock_log

        # Act
        result = await audit_service.log_delete(
            user=mock_user,
            entity_type=EntityType.COMPANY,
            entity_id=str(uuid4()),
            values=values,
            company_id=None,
        )

        # Assert
        assert result == mock_log
        assert mock_audit_repo.save.called
        saved_log = mock_audit_repo.save.call_args[0][0]
        assert saved_log.action == AuditAction.DELETE
        assert saved_log.username == mock_user.name

    @pytest.mark.asyncio
    async def test_get_all_logs_system_admin(self, audit_service, mock_audit_repo, mock_user):
        """System admin sees all logs."""
        # Arrange
        mock_user.role = UserRole.SYSTEM_ADMIN
        mock_logs = [Mock(spec=AuditLog), Mock(spec=AuditLog)]
        mock_audit_repo.get_all.return_value = mock_logs

        # Act
        result = await audit_service.get_all_logs(mock_user, skip=0, limit=10)

        # Assert
        assert result == mock_logs
        mock_audit_repo.get_all.assert_called_once_with(
            company_id=None,  # System admin sees all
            skip=0,
            limit=10
        )

    @pytest.mark.asyncio
    async def test_get_all_logs_company_admin(self, audit_service, mock_audit_repo, mock_user):
        """Company admin sees only their company's logs."""
        # Arrange
        mock_user.role = UserRole.COMPANY_ADMIN
        mock_logs = [Mock(spec=AuditLog)]
        mock_audit_repo.get_all.return_value = mock_logs

        # Act
        result = await audit_service.get_all_logs(mock_user, skip=5, limit=20)

        # Assert
        assert result == mock_logs
        mock_audit_repo.get_all.assert_called_once_with(
            company_id=str(mock_user.company_id),
            skip=5,
            limit=20
        )

    @pytest.mark.asyncio
    async def test_get_entity_logs_system_admin(self, audit_service, mock_audit_repo, mock_user):
        """System admin sees all entity logs."""
        # Arrange
        mock_user.role = UserRole.SYSTEM_ADMIN
        entity_id = str(uuid4())
        mock_logs = [Mock(spec=AuditLog)]
        mock_audit_repo.get_by_entity.return_value = mock_logs

        # Act
        result = await audit_service.get_entity_logs(
            mock_user,
            EntityType.USER,
            entity_id,
            skip=0,
            limit=50
        )

        # Assert
        assert result == mock_logs
        mock_audit_repo.get_by_entity.assert_called_once_with(
            entity_type=EntityType.USER,
            entity_id=entity_id,
            company_id=None,  # System admin sees all
            skip=0,
            limit=50
        )

    @pytest.mark.asyncio
    async def test_sensitive_data_filtering(self, audit_service, mock_audit_repo, mock_user):
        """Sensitive fields are filtered from audit logs."""
        # Arrange
        values = {
            "username": "john",
            "password": "secret",
            "hashed_password": "hash123",
            "token": "jwt_token",
            "refresh_token": "refresh",
            "api_key": "key123",
            "secret": "secret_value",
            "normal_field": "visible",
        }
        mock_log = Mock(spec=AuditLog)
        mock_audit_repo.save.return_value = mock_log

        # Act
        await audit_service.log_create(
            user=mock_user,
            entity_type=EntityType.USER,
            entity_id=str(uuid4()),
            values=values,
            company_id=None,
        )

        # Assert
        saved_log = mock_audit_repo.save.call_args[0][0]
        import json
        changes = json.loads(saved_log.changes)

        # Sensitive fields should be filtered
        assert "password" not in changes
        assert "hashed_password" not in changes
        assert "token" not in changes
        assert "refresh_token" not in changes
        assert "api_key" not in changes
        assert "secret" not in changes

        # Normal fields should remain
        assert changes["username"] == "john"
        assert changes["normal_field"] == "visible"
