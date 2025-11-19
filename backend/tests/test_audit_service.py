"""Tests for AuditService - audit trail business logic."""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from datetime import datetime

from features.audit.service import AuditService, SENSITIVE_FIELDS
from features.audit.models import AuditAction, AuditLog
from features.auth.models import User, UserRole
from features.company.models import Company


@pytest.fixture
def mock_company():
    """Create mock company."""
    company = Mock(spec=Company)
    company.id = uuid4()
    company.name = "Test Company"
    company.is_active = True
    return company


@pytest.fixture
def mock_user(mock_company):
    """Create mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.name = "John Doe"
    user.role = UserRole.COMPANY_ADMIN
    user.company_id = mock_company.id
    user.company = mock_company
    user.is_active = True
    return user


@pytest.fixture
def mock_system_admin():
    """Create mock system admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.name = "System Admin"
    user.role = UserRole.SYSTEM_ADMIN
    user.company_id = None
    user.company = None
    user.is_active = True
    return user


@pytest.fixture
def mock_audit_repo():
    """Create mock audit repository."""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_entity_history = AsyncMock(return_value=[])
    repo.get_logs = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def audit_service(mock_audit_repo):
    """Create AuditService with mocked repository."""
    return AuditService(mock_audit_repo)


class TestAuditService:
    """Test AuditService business logic."""

    # ========================================================================
    # Sensitive Field Filtering Tests
    # ========================================================================

    def test_sanitize_values_removes_password(self, audit_service):
        """Sanitize removes password field."""
        # Arrange
        values = {
            "username": "john",
            "password": "secret123",
            "email": "john@test.com",
        }

        # Act
        sanitized = audit_service._sanitize_values(values)

        # Assert
        assert "password" not in sanitized
        assert "username" in sanitized
        assert "email" in sanitized

    def test_sanitize_values_removes_hashed_password(self, audit_service):
        """Sanitize removes hashed_password field."""
        # Arrange
        values = {
            "username": "john",
            "hashed_password": "$2b$12$abc123",
            "email": "john@test.com",
        }

        # Act
        sanitized = audit_service._sanitize_values(values)

        # Assert
        assert "hashed_password" not in sanitized
        assert "username" in sanitized

    def test_sanitize_values_removes_all_sensitive_fields(self, audit_service):
        """Sanitize removes all sensitive fields."""
        # Arrange
        values = {
            "username": "john",
            "password": "secret",
            "hashed_password": "$2b$12$abc",
            "password_hash": "hash",
            "token": "token123",
            "secret": "secret123",
            "api_key": "key123",
            "email": "john@test.com",
        }

        # Act
        sanitized = audit_service._sanitize_values(values)

        # Assert
        for field in SENSITIVE_FIELDS:
            assert field not in sanitized
        assert "username" in sanitized
        assert "email" in sanitized

    def test_sanitize_values_case_insensitive(self, audit_service):
        """Sanitize handles fields case-insensitively."""
        # Arrange
        values = {
            "PASSWORD": "secret",
            "Token": "token123",
            "API_KEY": "key123",
            "username": "john",
        }

        # Act
        sanitized = audit_service._sanitize_values(values)

        # Assert
        assert "PASSWORD" not in sanitized
        assert "Token" not in sanitized
        assert "API_KEY" not in sanitized
        assert "username" in sanitized

    # ========================================================================
    # Change Detection Tests
    # ========================================================================

    def test_compute_changes_detects_updates(self, audit_service):
        """Compute changes detects field updates."""
        # Arrange
        old_values = {"price": 100, "name": "Widget", "stock": 50}
        new_values = {"price": 120, "name": "Widget", "stock": 30}

        # Act
        changes = audit_service._compute_changes(old_values, new_values)

        # Assert
        assert "price" in changes
        assert changes["price"]["old"] == 100
        assert changes["price"]["new"] == 120
        assert "stock" in changes
        assert changes["stock"]["old"] == 50
        assert changes["stock"]["new"] == 30
        assert "name" not in changes  # No change

    def test_compute_changes_detects_additions(self, audit_service):
        """Compute changes detects new fields."""
        # Arrange
        old_values = {"name": "Widget"}
        new_values = {"name": "Widget", "price": 100}

        # Act
        changes = audit_service._compute_changes(old_values, new_values)

        # Assert
        assert "price" in changes
        assert changes["price"]["old"] is None
        assert changes["price"]["new"] == 100

    def test_compute_changes_detects_removals(self, audit_service):
        """Compute changes detects removed fields."""
        # Arrange
        old_values = {"name": "Widget", "deprecated": True}
        new_values = {"name": "Widget"}

        # Act
        changes = audit_service._compute_changes(old_values, new_values)

        # Assert
        assert "deprecated" in changes
        assert changes["deprecated"]["old"] is True
        assert changes["deprecated"]["new"] is None

    def test_compute_changes_no_changes(self, audit_service):
        """Compute changes returns empty dict when no changes."""
        # Arrange
        old_values = {"name": "Widget", "price": 100}
        new_values = {"name": "Widget", "price": 100}

        # Act
        changes = audit_service._compute_changes(old_values, new_values)

        # Assert
        assert changes == {}

    # ========================================================================
    # Log Create Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_log_create_success(self, audit_service, mock_audit_repo, mock_user):
        """Log create succeeds and sanitizes values."""
        # Arrange
        values = {
            "name": "New Product",
            "price": 100,
            "password": "secret123",  # Should be filtered
        }
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_create(
            user=mock_user,
            entity_type="Product",
            entity_id=str(uuid4()),
            values=values,
            company_id=mock_user.company_id,
        )

        # Assert
        assert mock_audit_repo.create.called
        created_log = mock_audit_repo.create.call_args[0][0]
        assert created_log.action == AuditAction.CREATE
        assert created_log.entity_type == "Product"
        assert created_log.user_id == mock_user.id
        assert created_log.username == mock_user.name
        assert created_log.company_id == mock_user.company_id
        assert created_log.old_values is None
        assert "password" not in created_log.new_values
        assert created_log.new_values["name"] == "New Product"
        assert created_log.changes is None

    @pytest.mark.asyncio
    async def test_log_create_system_admin(self, audit_service, mock_audit_repo, mock_system_admin):
        """Log create for system admin has no company."""
        # Arrange
        values = {"name": "System Config"}
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_create(
            user=mock_system_admin,
            entity_type="SystemConfig",
            entity_id=str(uuid4()),
            values=values,
        )

        # Assert
        created_log = mock_audit_repo.create.call_args[0][0]
        assert created_log.company_id is None
        assert created_log.company_name is None

    # ========================================================================
    # Log Update Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_log_update_success(self, audit_service, mock_audit_repo, mock_user):
        """Log update computes changes correctly."""
        # Arrange
        old_values = {"name": "Widget", "price": 100, "stock": 50}
        new_values = {"name": "Widget Pro", "price": 100, "stock": 30}
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_update(
            user=mock_user,
            entity_type="Product",
            entity_id=str(uuid4()),
            old_values=old_values,
            new_values=new_values,
            company_id=mock_user.company_id,
        )

        # Assert
        created_log = mock_audit_repo.create.call_args[0][0]
        assert created_log.action == AuditAction.UPDATE
        assert "name" in created_log.changes
        assert created_log.changes["name"]["old"] == "Widget"
        assert created_log.changes["name"]["new"] == "Widget Pro"
        assert "stock" in created_log.changes
        assert "price" not in created_log.changes  # No change

    @pytest.mark.asyncio
    async def test_log_update_sanitizes_passwords(self, audit_service, mock_audit_repo, mock_user):
        """Log update removes passwords from old and new values."""
        # Arrange
        old_values = {"username": "john", "password": "old_secret"}
        new_values = {"username": "john", "password": "new_secret"}
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_update(
            user=mock_user,
            entity_type="User",
            entity_id=str(uuid4()),
            old_values=old_values,
            new_values=new_values,
            company_id=mock_user.company_id,
        )

        # Assert
        created_log = mock_audit_repo.create.call_args[0][0]
        assert "password" not in created_log.old_values
        assert "password" not in created_log.new_values
        assert "password" not in created_log.changes
        assert created_log.old_values["username"] == "john"

    # ========================================================================
    # Log Delete Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_log_delete_success(self, audit_service, mock_audit_repo, mock_user):
        """Log delete stores old values."""
        # Arrange
        old_values = {"name": "Deleted Product", "price": 100}
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_delete(
            user=mock_user,
            entity_type="Product",
            entity_id=str(uuid4()),
            old_values=old_values,
            company_id=mock_user.company_id,
        )

        # Assert
        created_log = mock_audit_repo.create.call_args[0][0]
        assert created_log.action == AuditAction.DELETE
        assert created_log.old_values["name"] == "Deleted Product"
        assert created_log.new_values is None
        assert created_log.changes is None

    @pytest.mark.asyncio
    async def test_log_delete_sanitizes_values(self, audit_service, mock_audit_repo, mock_user):
        """Log delete removes sensitive fields."""
        # Arrange
        old_values = {"username": "john", "hashed_password": "$2b$12$abc"}
        mock_audit_repo.create.return_value = Mock(spec=AuditLog)

        # Act
        await audit_service.log_delete(
            user=mock_user,
            entity_type="User",
            entity_id=str(uuid4()),
            old_values=old_values,
            company_id=mock_user.company_id,
        )

        # Assert
        created_log = mock_audit_repo.create.call_args[0][0]
        assert "hashed_password" not in created_log.old_values
        assert created_log.old_values["username"] == "john"

    # ========================================================================
    # Get Entity History Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_entity_history_system_admin(
        self, audit_service, mock_audit_repo, mock_system_admin
    ):
        """System admin can see all entity history."""
        # Arrange
        mock_logs = [Mock(spec=AuditLog, company_id=uuid4()) for _ in range(3)]
        mock_audit_repo.get_entity_history.return_value = mock_logs

        # Act
        history = await audit_service.get_entity_history(
            entity_type="Product",
            entity_id=str(uuid4()),
            current_user=mock_system_admin,
        )

        # Assert
        assert len(history) == 3  # Sees all logs

    @pytest.mark.asyncio
    async def test_get_entity_history_company_user_filtered(
        self, audit_service, mock_audit_repo, mock_user
    ):
        """Company user only sees their company's entity history."""
        # Arrange
        company_a = mock_user.company_id
        company_b = uuid4()

        mock_logs = [
            Mock(spec=AuditLog, company_id=company_a),
            Mock(spec=AuditLog, company_id=company_b),
            Mock(spec=AuditLog, company_id=company_a),
        ]
        mock_audit_repo.get_entity_history.return_value = mock_logs

        # Act
        history = await audit_service.get_entity_history(
            entity_type="Product",
            entity_id=str(uuid4()),
            current_user=mock_user,
        )

        # Assert
        assert len(history) == 2  # Only sees company A logs
        assert all(log.company_id == company_a for log in history)

    # ========================================================================
    # Get Audit Logs Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_audit_logs_system_admin(
        self, audit_service, mock_audit_repo, mock_system_admin
    ):
        """System admin can query all audit logs."""
        # Arrange
        mock_logs = [Mock(spec=AuditLog) for _ in range(5)]
        mock_audit_repo.get_logs.return_value = (mock_logs, 5)

        # Act
        logs, total = await audit_service.get_audit_logs(
            current_user=mock_system_admin,
            company_id=None,  # No filter
        )

        # Assert
        assert len(logs) == 5
        assert total == 5
        # Should pass None for company_id (no filtering)
        assert mock_audit_repo.get_logs.call_args[1]["company_id"] is None

    @pytest.mark.asyncio
    async def test_get_audit_logs_company_admin_forced_filter(
        self, audit_service, mock_audit_repo, mock_user
    ):
        """Company admin's queries are automatically filtered to their company."""
        # Arrange
        mock_logs = [Mock(spec=AuditLog) for _ in range(3)]
        mock_audit_repo.get_logs.return_value = (mock_logs, 3)

        # Act - Try to query without company filter
        logs, total = await audit_service.get_audit_logs(
            current_user=mock_user,
            company_id=None,  # Intentionally no filter
        )

        # Assert
        # Service should force company_id filter
        assert mock_audit_repo.get_logs.call_args[1]["company_id"] == mock_user.company_id

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(
        self, audit_service, mock_audit_repo, mock_system_admin
    ):
        """Get audit logs passes all filters to repository."""
        # Arrange
        mock_logs = [Mock(spec=AuditLog)]
        mock_audit_repo.get_logs.return_value = (mock_logs, 1)
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        test_company_id = uuid4()
        test_user_id = uuid4()

        # Act
        await audit_service.get_audit_logs(
            current_user=mock_system_admin,
            company_id=test_company_id,
            entity_type="Product",
            user_id=test_user_id,
            action=AuditAction.UPDATE,
            start_date=start_date,
            end_date=end_date,
            limit=50,
            offset=10,
        )

        # Assert
        call_kwargs = mock_audit_repo.get_logs.call_args[1]
        assert call_kwargs["company_id"] == test_company_id
        assert call_kwargs["entity_type"] == "Product"
        assert call_kwargs["user_id"] == test_user_id
        assert call_kwargs["action"] == AuditAction.UPDATE
        assert call_kwargs["start_date"] == start_date
        assert call_kwargs["end_date"] == end_date
        assert call_kwargs["limit"] == 50
        assert call_kwargs["offset"] == 10
