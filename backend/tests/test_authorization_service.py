"""Tests for AuthorizationService - permission checking logic."""
import pytest
from unittest.mock import Mock
from uuid import uuid4
from features.authorization.service import AuthorizationService, create_authorization_service
from features.authorization.permissions import Permission
from features.auth.models import User, UserRole


@pytest.fixture
def mock_system_admin():
    """Create mock system admin user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000001"
    user.role = UserRole.SYSTEM_ADMIN
    user.company_id = None
    
    user.is_active = True
    return user


@pytest.fixture
def mock_company_admin():
    """Create mock company admin user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000002"
    user.role = UserRole.COMPANY_ADMIN
    user.company_id = uuid4()
    user.is_active = True
    return user


@pytest.fixture
def mock_accountant():
    """Create mock user with accountant role."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000003"
    user.role = UserRole.ACCOUNTANT
    user.company_id = uuid4()
    user.is_active = True
    return user


@pytest.fixture
def mock_salesperson():
    """Create mock user with salesperson role."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000004"
    user.role = UserRole.SALESPERSON
    user.company_id = uuid4()
    user.is_active = True
    return user


@pytest.fixture
def mock_viewer():
    """Create mock user with viewer role."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000005"
    user.role = UserRole.VIEWER
    user.company_id = uuid4()
    user.is_active = True
    return user


@pytest.fixture
def mock_inactive_user():
    """Create mock inactive user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.phone_number = "+9647700000006"
    user.role = UserRole.VIEWER
    user.company_id = uuid4()
    user.is_active = False  # Inactive
    return user


class TestAuthorizationService:
    """Test AuthorizationService permission logic."""

    def test_system_admin_has_all_permissions(self, mock_system_admin):
        """System admin should have all permissions."""
        # Arrange
        auth_service = AuthorizationService(mock_system_admin)

        # Act & Assert - test a few permissions
        assert auth_service.has_permission(Permission.VIEW_USERS)
        assert auth_service.has_permission(Permission.CREATE_USERS)
        assert auth_service.has_permission(Permission.DELETE_USERS)
        assert auth_service.has_permission(Permission.VIEW_COMPANIES)
        assert auth_service.has_permission(Permission.CREATE_COMPANIES)
        assert auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert auth_service.has_permission(Permission.EDIT_SYSTEM_SETTINGS)

        # Verify is_system_admin
        assert auth_service.is_system_admin()

        # Check that ALL permissions are present
        all_permissions = list(Permission)
        assert len(auth_service.permissions) == len(all_permissions)

    def test_null_user_has_no_permissions(self):
        """User = None should have zero permissions."""
        # Arrange
        auth_service = AuthorizationService(user=None)

        # Act & Assert
        assert len(auth_service.permissions) == 0
        assert not auth_service.has_permission(Permission.VIEW_USERS)
        assert not auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert not auth_service.is_system_admin()

    def test_inactive_user_has_no_permissions(self, mock_inactive_user):
        """Inactive users should have zero permissions regardless of role."""
        # Arrange
        auth_service = AuthorizationService(mock_inactive_user)

        # Act & Assert
        assert len(auth_service.permissions) == 0
        assert not auth_service.has_permission(Permission.VIEW_USERS)
        assert not auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert not auth_service.is_system_admin()

    def test_user_from_inactive_company_has_no_permissions(self):
        """Users from inactive companies should have zero permissions."""
        # Arrange - Create user with inactive company
        from features.company.models import Company
        company_id = uuid4()

        # Mock inactive company
        inactive_company = Mock(spec=Company)
        inactive_company.id = company_id
        inactive_company.is_active = False

        user = Mock(spec=User)
        user.id = str(uuid4())
        user.phone_number = "+9647700000010"
        user.role = UserRole.COMPANY_ADMIN  # Even admin role gets no permissions
        user.company_id = company_id
        user.company = inactive_company
        user.is_active = True  # User is active, but company is not

        auth_service = AuthorizationService(user)

        # Act & Assert
        assert len(auth_service.permissions) == 0
        assert not auth_service.has_permission(Permission.VIEW_USERS)
        assert not auth_service.has_permission(Permission.CREATE_USERS)
        assert not auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert not auth_service.is_system_admin()

    def test_company_admin_permissions(self, mock_company_admin):
        """Company admin should have admin permissions within company."""
        # Arrange
        auth_service = AuthorizationService(mock_company_admin)

        # Act & Assert - Company admin has these permissions
        assert auth_service.has_permission(Permission.VIEW_USERS)
        assert auth_service.has_permission(Permission.EDIT_USERS)
        assert auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert auth_service.has_permission(Permission.CREATE_PRODUCTS)
        assert auth_service.has_permission(Permission.EDIT_PRODUCTS)
        assert auth_service.has_permission(Permission.DELETE_PRODUCTS)
        assert auth_service.has_permission(Permission.VIEW_INVOICES)
        assert auth_service.has_permission(Permission.CREATE_INVOICES)
        assert auth_service.has_permission(Permission.VIEW_WAREHOUSE)
        assert auth_service.has_permission(Permission.MANAGE_WAREHOUSE)

        # Company admin CAN create/edit/delete users within their company
        assert auth_service.has_permission(Permission.CREATE_USERS)
        assert auth_service.has_permission(Permission.DELETE_USERS)

        # Company admin CANNOT manage companies (system admin only)
        assert not auth_service.has_permission(Permission.VIEW_COMPANIES)
        assert not auth_service.has_permission(Permission.CREATE_COMPANIES)
        assert not auth_service.has_permission(Permission.EDIT_SYSTEM_SETTINGS)

        # Not a system admin
        assert not auth_service.is_system_admin()

    def test_accountant_permissions(self, mock_accountant):
        """Accountant should have financial and reporting permissions."""
        # Arrange
        auth_service = AuthorizationService(mock_accountant)

        # Act & Assert - Accountant has these permissions
        assert auth_service.has_permission(Permission.VIEW_USERS)
        assert auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert auth_service.has_permission(Permission.VIEW_INVOICES)
        assert auth_service.has_permission(Permission.VIEW_PURCHASES)
        assert auth_service.has_permission(Permission.VIEW_REPORTS)
        assert auth_service.has_permission(Permission.EXPORT_REPORTS)
        assert auth_service.has_permission(Permission.VIEW_FINANCIALS)

        # Accountant CANNOT create/edit/delete products
        assert not auth_service.has_permission(Permission.CREATE_PRODUCTS)
        assert not auth_service.has_permission(Permission.EDIT_PRODUCTS)
        assert not auth_service.has_permission(Permission.DELETE_PRODUCTS)

        # Accountant CANNOT manage warehouse
        assert not auth_service.has_permission(Permission.MANAGE_WAREHOUSE)

        # Accountant CANNOT manage users
        assert not auth_service.has_permission(Permission.CREATE_USERS)
        assert not auth_service.has_permission(Permission.EDIT_USERS)

    def test_salesperson_permissions(self, mock_salesperson):
        """Salesperson should have limited sales permissions."""
        # Arrange
        auth_service = AuthorizationService(mock_salesperson)

        # Act & Assert - Salesperson has these permissions
        assert auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert auth_service.has_permission(Permission.VIEW_INVOICES)
        assert auth_service.has_permission(Permission.CREATE_INVOICES)
        assert auth_service.has_permission(Permission.VIEW_WAREHOUSE)

        # Salesperson CANNOT edit/delete invoices
        assert not auth_service.has_permission(Permission.EDIT_INVOICES)
        assert not auth_service.has_permission(Permission.DELETE_INVOICES)

        # Salesperson CANNOT manage products
        assert not auth_service.has_permission(Permission.CREATE_PRODUCTS)
        assert not auth_service.has_permission(Permission.EDIT_PRODUCTS)

        # Salesperson CANNOT view financial reports
        assert not auth_service.has_permission(Permission.VIEW_FINANCIALS)

    def test_viewer_permissions(self, mock_viewer):
        """Viewer should have read-only permissions."""
        # Arrange
        auth_service = AuthorizationService(mock_viewer)

        # Act & Assert - Viewer can view
        assert auth_service.has_permission(Permission.VIEW_USERS)
        assert auth_service.has_permission(Permission.VIEW_PRODUCTS)
        assert auth_service.has_permission(Permission.VIEW_INVOICES)
        assert auth_service.has_permission(Permission.VIEW_PURCHASES)
        assert auth_service.has_permission(Permission.VIEW_WAREHOUSE)
        assert auth_service.has_permission(Permission.VIEW_REPORTS)

        # Viewer CANNOT create/edit/delete anything
        assert not auth_service.has_permission(Permission.CREATE_USERS)
        assert not auth_service.has_permission(Permission.EDIT_USERS)
        assert not auth_service.has_permission(Permission.DELETE_USERS)
        assert not auth_service.has_permission(Permission.CREATE_PRODUCTS)
        assert not auth_service.has_permission(Permission.EDIT_PRODUCTS)
        assert not auth_service.has_permission(Permission.DELETE_PRODUCTS)
        assert not auth_service.has_permission(Permission.CREATE_INVOICES)


    def test_has_permission_with_string(self, mock_accountant):
        """has_permission should accept permission string."""
        # Arrange
        auth_service = AuthorizationService(mock_accountant)

        # Act & Assert - Test with string
        assert auth_service.has_permission("users.view")
        assert auth_service.has_permission("products.view")
        assert not auth_service.has_permission("products.create")

        # Invalid permission string should return False
        assert not auth_service.has_permission("invalid.permission")

    def test_has_any_permission(self, mock_salesperson):
        """has_any_permission should return True if user has at least one."""
        # Arrange
        auth_service = AuthorizationService(mock_salesperson)

        # Act & Assert
        # Has CREATE_INVOICES but not DELETE_INVOICES
        assert auth_service.has_any_permission([
            Permission.CREATE_INVOICES,
            Permission.DELETE_INVOICES,
        ])

        # Has none of these
        assert not auth_service.has_any_permission([
            Permission.CREATE_USERS,
            Permission.DELETE_USERS,
        ])

    def test_has_all_permissions(self, mock_salesperson):
        """has_all_permissions should return True only if user has all."""
        # Arrange
        auth_service = AuthorizationService(mock_salesperson)

        # Act & Assert
        # Has both of these
        assert auth_service.has_all_permissions([
            Permission.VIEW_PRODUCTS,
            Permission.VIEW_INVOICES,
        ])

        # Missing DELETE_INVOICES
        assert not auth_service.has_all_permissions([
            Permission.VIEW_INVOICES,
            Permission.DELETE_INVOICES,
        ])

    def test_get_permission_list(self, mock_accountant):
        """get_permission_list should return list of permission strings."""
        # Arrange
        auth_service = AuthorizationService(mock_accountant)

        # Act
        permissions = auth_service.get_permission_list()

        # Assert
        assert isinstance(permissions, list)
        assert len(permissions) > 0
        assert "users.view" in permissions
        assert "products.view" in permissions
        assert "reports.view" in permissions

        # Should not have product management permissions
        assert "products.create" not in permissions

    def test_permissions_cached(self, mock_company_admin):
        """Permissions should be calculated once and cached."""
        # Arrange
        auth_service = AuthorizationService(mock_company_admin)

        # Act - Access permissions multiple times
        perms1 = auth_service.permissions
        perms2 = auth_service.permissions

        # Assert - Should return same object (cached)
        assert perms1 is perms2

    def test_create_authorization_service_factory(self, mock_system_admin):
        """create_authorization_service factory should work."""
        # Act
        auth_service = create_authorization_service(mock_system_admin)

        # Assert
        assert isinstance(auth_service, AuthorizationService)
        assert auth_service.user == mock_system_admin
        assert auth_service.has_permission(Permission.VIEW_USERS)
