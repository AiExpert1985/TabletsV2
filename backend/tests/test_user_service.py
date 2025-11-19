"""Tests for UserService - user management business logic."""
import pytest
from unittest.mock import AsyncMock, Mock
from features.users.service import UserService
from features.users.models import User
from core.enums import UserRole
from core.exceptions import PhoneAlreadyExistsException, UserNotFoundException


@pytest.fixture
def mock_user_repo():
    """Create mock user repository."""
    repo = Mock()
    repo.phone_exists = AsyncMock(return_value=False)
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_service():
    """Create mock audit service."""
    service = Mock()
    service.log_create = AsyncMock()
    service.log_update = AsyncMock()
    service.log_delete = AsyncMock()
    return service


@pytest.fixture
def mock_current_user():
    """Create a mock user representing the current logged-in user performing actions."""
    from uuid import uuid4
    user = Mock(spec=User)
    user.id = uuid4()
    user.name = "Admin User"
    user.phone_number = "+9647700000000"
    user.role = UserRole.SYSTEM_ADMIN
    user.company_id = None
    user.is_active = True
    return user


@pytest.fixture
def user_service(mock_user_repo, mock_audit_service):
    """Create UserService with mocked repository and audit service."""
    return UserService(mock_user_repo, mock_audit_service)


class TestUserService:
    """Test UserService business logic."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repo, mock_current_user):
        """Create user with valid data succeeds."""
        # Arrange
        mock_user_repo.phone_exists.return_value = False
        mock_user = Mock(spec=User)
        mock_user_repo.save.return_value = mock_user

        # Act
        user = await user_service.create_user(
            name="Test User",
            phone_number="07700000001",
            password="TestPass123",
            company_id="123e4567-e89b-12d3-a456-426614174000",
            role="viewer",
            current_user=mock_current_user,
        )

        # Assert
        assert mock_user_repo.phone_exists.called
        assert mock_user_repo.save.called
        assert user == mock_user

    @pytest.mark.asyncio
    async def test_create_user_phone_exists_raises_exception(self, user_service, mock_user_repo, mock_current_user):
        """Creating user with existing phone raises PhoneAlreadyExistsException."""
        # Arrange
        mock_user_repo.phone_exists.return_value = True

        # Act & Assert
        with pytest.raises(PhoneAlreadyExistsException):
            await user_service.create_user(
                name="Test User",
                phone_number="07700000001",
                password="TestPass123",
                company_id="123e4567-e89b-12d3-a456-426614174000",
                role="viewer",
                current_user=mock_current_user,
            )

    @pytest.mark.asyncio
    async def test_create_system_admin_with_company_raises_error(self, user_service, mock_user_repo, mock_current_user):
        """Creating system admin with company_id raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="System admin cannot have a company_id"):
            await user_service.create_user(
                name="System Admin",
                phone_number="07700000001",
                password="TestPass123",
                company_id="123e4567-e89b-12d3-a456-426614174000",
                role="system_admin",
                current_user=mock_current_user,
            )

    @pytest.mark.asyncio
    async def test_create_regular_user_without_company_raises_error(self, user_service, mock_user_repo, mock_current_user):
        """Creating regular user without company_id raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="must have a company_id"):
            await user_service.create_user(
                name="Test User",
                phone_number="07700000001",
                password="TestPass123",
                company_id=None,
                role="viewer",
                current_user=mock_current_user,
            )

    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_user_repo):
        """Get user by ID returns user."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_user.id = "123"
        mock_user_repo.get_by_id.return_value = mock_user

        # Act
        user = await user_service.get_user("123")

        # Assert
        assert user == mock_user
        mock_user_repo.get_by_id.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_get_user_not_found_raises_exception(self, user_service, mock_user_repo):
        """Get user with invalid ID raises UserNotFoundException."""
        # Arrange
        mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundException):
            await user_service.get_user("invalid-id")

    @pytest.mark.asyncio
    async def test_list_users(self, user_service, mock_user_repo):
        """List users returns users from repository."""
        # Arrange
        mock_users = [Mock(spec=User), Mock(spec=User)]
        mock_user_repo.get_all.return_value = mock_users

        # Act
        users = await user_service.list_users(skip=0, limit=10)

        # Assert
        assert users == mock_users
        mock_user_repo.get_all.assert_called_once_with(0, 10)

    @pytest.mark.asyncio
    async def test_update_user_password_hashed(self, user_service, mock_user_repo, mock_current_user):
        """Update user password hashes the password."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_user.id = "123"
        mock_user.phone_number = "+9647700000001"
        mock_user.company_id = None
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = mock_user

        # Act
        await user_service.update_user(
            user_id="123",
            current_user=mock_current_user,
            password="NewPassword123"
        )

        # Assert
        assert mock_user.hashed_password is not None
        assert mock_user.hashed_password != "NewPassword123"  # Should be hashed
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repo):
        """Delete user calls repository delete."""
        # Arrange
        from uuid import uuid4
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_current_user = Mock(spec=User)
        mock_current_user.id = uuid4()
        mock_user_repo.get_by_id.return_value = mock_user

        # Act
        await user_service.delete_user(str(mock_user.id), mock_current_user)

        # Assert
        mock_user_repo.delete.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_delete_user_self_deletion_raises_error(self, user_service, mock_user_repo):
        """Deleting yourself raises ValueError."""
        # Arrange
        from uuid import uuid4
        user_id = uuid4()
        mock_current_user = Mock(spec=User)
        mock_current_user.id = user_id

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete yourself"):
            await user_service.delete_user(str(user_id), mock_current_user)
