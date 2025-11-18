"""Tests for CompanyContext - multi-tenant data isolation logic."""
import pytest
from unittest.mock import Mock
from uuid import uuid4
from fastapi import HTTPException
from core.company_context import CompanyContext, get_company_context
from features.auth.models import User, UserRole


@pytest.fixture
def mock_system_admin():
    """Create mock system admin user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000001"
    user.role = UserRole.SYSTEM_ADMIN
    user.company_id = None  # System admin has no company
    user.company_roles = []
    user.is_active = True
    return user


@pytest.fixture
def mock_company_user():
    """Create mock regular company user."""
    company_id = uuid4()
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000002"
    user.role = UserRole.USER
    user.company_id = company_id
    user.company_roles = ["viewer"]
    user.is_active = True
    return user


@pytest.fixture
def mock_company_admin():
    """Create mock company admin user."""
    company_id = uuid4()
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000003"
    user.role = UserRole.COMPANY_ADMIN
    user.company_id = company_id
    user.company_roles = ["admin"]
    user.is_active = True
    return user


class TestCompanyContext:
    """Test CompanyContext multi-tenancy isolation."""

    def test_system_admin_no_filtering(self, mock_system_admin):
        """System admin should have no company filtering."""
        # Arrange & Act
        ctx = CompanyContext(mock_system_admin)

        # Assert
        assert ctx.is_system_admin is True
        assert ctx.company_id is None
        assert ctx.should_filter is False

    def test_regular_user_has_filtering(self, mock_company_user):
        """Regular company user should have company filtering."""
        # Arrange & Act
        ctx = CompanyContext(mock_company_user)

        # Assert
        assert ctx.is_system_admin is False
        assert ctx.company_id == mock_company_user.company_id
        assert ctx.should_filter is True

    def test_company_admin_has_filtering(self, mock_company_admin):
        """Company admin should have company filtering (not global access)."""
        # Arrange & Act
        ctx = CompanyContext(mock_company_admin)

        # Assert
        assert ctx.is_system_admin is False
        assert ctx.company_id == mock_company_admin.company_id
        assert ctx.should_filter is True

    def test_regular_user_without_company_raises_error(self):
        """Regular user without company_id should raise 500 error."""
        # Arrange - User without company_id (data corruption)
        user = Mock(spec=User)
        user.id = str(uuid4())
        user.role = UserRole.USER
        user.company_id = None  # Invalid for regular user
        user.is_active = True

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            CompanyContext(user)

        assert exc_info.value.status_code == 500
        assert "configuration error" in exc_info.value.detail.lower()

    def test_filter_query_by_company_for_regular_user(self, mock_company_user):
        """filter_query_by_company should add WHERE clause for regular users."""
        # Arrange
        ctx = CompanyContext(mock_company_user)

        # Mock SQLAlchemy query and model
        mock_query = Mock()
        mock_model = Mock()
        mock_model.company_id = "company_id_column"

        # Mock the where() method to return a new query
        filtered_query = Mock()
        mock_query.where.return_value = filtered_query

        # Act
        result = ctx.filter_query_by_company(mock_query, mock_model)

        # Assert
        assert mock_query.where.called
        assert result == filtered_query

    def test_filter_query_by_company_for_system_admin(self, mock_system_admin):
        """filter_query_by_company should NOT filter for system admin."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Mock SQLAlchemy query and model
        mock_query = Mock()
        mock_model = Mock()

        # Act
        result = ctx.filter_query_by_company(mock_query, mock_model)

        # Assert
        assert not mock_query.where.called  # No filtering
        assert result == mock_query  # Returns original query

    def test_ensure_company_access_same_company_succeeds(self, mock_company_user):
        """ensure_company_access should succeed for same company."""
        # Arrange
        ctx = CompanyContext(mock_company_user)
        resource_company_id = mock_company_user.company_id

        # Act & Assert - Should not raise
        ctx.ensure_company_access(resource_company_id)

    def test_ensure_company_access_different_company_raises_403(self, mock_company_user):
        """ensure_company_access should raise 403 for different company."""
        # Arrange
        ctx = CompanyContext(mock_company_user)
        other_company_id = uuid4()  # Different company

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            ctx.ensure_company_access(other_company_id)

        assert exc_info.value.status_code == 403
        assert "permission" in exc_info.value.detail.lower()

    def test_ensure_company_access_system_admin_can_access_any(self, mock_system_admin):
        """System admin should access any company's resources."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)
        any_company_id = uuid4()

        # Act & Assert - Should not raise
        ctx.ensure_company_access(any_company_id)

    def test_ensure_company_access_null_resource_company_for_regular_user(self, mock_company_user):
        """Regular user accessing resource with null company_id should raise 403."""
        # Arrange
        ctx = CompanyContext(mock_company_user)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            ctx.ensure_company_access(None)

        assert exc_info.value.status_code == 403

    def test_ensure_company_access_null_resource_company_for_system_admin(self, mock_system_admin):
        """System admin can access resource with null company_id."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Act & Assert - Should not raise
        ctx.ensure_company_access(None)

    def test_get_company_id_for_create_regular_user(self, mock_company_user):
        """Regular user should use their company_id for creating resources."""
        # Arrange
        ctx = CompanyContext(mock_company_user)

        # Act
        company_id = ctx.get_company_id_for_create()

        # Assert
        assert company_id == mock_company_user.company_id

    def test_get_company_id_for_create_system_admin_raises_400(self, mock_system_admin):
        """System admin creating resource without company_id should raise 400."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            ctx.get_company_id_for_create()

        assert exc_info.value.status_code == 400
        assert "specify company_id" in exc_info.value.detail.lower()

    def test_repr_system_admin(self, mock_system_admin):
        """String representation for system admin should indicate no filtering."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Act
        repr_str = repr(ctx)

        # Assert
        assert "SYSTEM_ADMIN" in repr_str
        assert "no filtering" in repr_str.lower()

    def test_repr_regular_user(self, mock_company_user):
        """String representation for regular user should show company_id."""
        # Arrange
        ctx = CompanyContext(mock_company_user)

        # Act
        repr_str = repr(ctx)

        # Assert
        assert "CompanyContext" in repr_str
        assert "company_id" in repr_str
        assert str(mock_company_user.company_id) in repr_str

    def test_get_company_context_factory(self, mock_company_user):
        """get_company_context factory should create CompanyContext."""
        # Act
        ctx = get_company_context(mock_company_user)

        # Assert
        assert isinstance(ctx, CompanyContext)
        assert ctx.company_id == mock_company_user.company_id
        assert ctx.user == mock_company_user

    def test_should_filter_property_regular_user(self, mock_company_user):
        """should_filter property should be True for regular users."""
        # Arrange
        ctx = CompanyContext(mock_company_user)

        # Act & Assert
        assert ctx.should_filter is True

    def test_should_filter_property_system_admin(self, mock_system_admin):
        """should_filter property should be False for system admin."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Act & Assert
        assert ctx.should_filter is False

    def test_company_isolation_prevents_cross_company_access(self):
        """Integration test: Users from different companies cannot access each other's data."""
        # Arrange - Two users from different companies
        company_a_id = uuid4()
        company_b_id = uuid4()

        user_a = Mock(spec=User)
        user_a.id = str(uuid4())
        user_a.role = UserRole.USER
        user_a.company_id = company_a_id
        user_a.is_active = True

        user_b = Mock(spec=User)
        user_b.id = str(uuid4())
        user_b.role = UserRole.USER
        user_b.company_id = company_b_id
        user_b.is_active = True

        ctx_a = CompanyContext(user_a)
        ctx_b = CompanyContext(user_b)

        # Act & Assert - User A cannot access company B's resources
        with pytest.raises(HTTPException) as exc_info:
            ctx_a.ensure_company_access(company_b_id)
        assert exc_info.value.status_code == 403

        # User B cannot access company A's resources
        with pytest.raises(HTTPException) as exc_info:
            ctx_b.ensure_company_access(company_a_id)
        assert exc_info.value.status_code == 403

        # Each user can access their own company's resources
        ctx_a.ensure_company_access(company_a_id)  # Should not raise
        ctx_b.ensure_company_access(company_b_id)  # Should not raise

    def test_system_admin_bypasses_all_company_isolation(self, mock_system_admin):
        """Integration test: System admin can access all companies' data."""
        # Arrange
        ctx = CompanyContext(mock_system_admin)

        # Create multiple company IDs
        company_ids = [uuid4() for _ in range(5)]

        # Act & Assert - System admin can access all
        for company_id in company_ids:
            ctx.ensure_company_access(company_id)  # Should not raise

        # System admin doesn't filter queries
        assert ctx.should_filter is False

        # Mock query should not be filtered
        mock_query = Mock()
        result = ctx.filter_query_by_company(mock_query, Mock())
        assert result == mock_query
        assert not mock_query.where.called
