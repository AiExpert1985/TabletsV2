"""Tests for CompanyService - company management business logic."""
import pytest
from unittest.mock import AsyncMock, Mock
from features.company.service import CompanyService, CompanyAlreadyExistsException, CompanyNotFoundException
from features.company.models import Company


@pytest.fixture
def mock_company_repo():
    """Create mock company repository."""
    repo = Mock()
    repo.get_by_name = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def company_service(mock_company_repo):
    """Create CompanyService with mocked repository."""
    return CompanyService(mock_company_repo)


class TestCompanyService:
    """Test CompanyService business logic."""

    @pytest.mark.asyncio
    async def test_create_company_success(self, company_service, mock_company_repo):
        """Create company with unique name succeeds."""
        # Arrange
        mock_company = Mock(spec=Company)
        mock_company.name = "Test Company"
        mock_company_repo.get_by_name.return_value = None
        mock_company_repo.create.return_value = mock_company

        # Act
        company = await company_service.create_company("Test Company")

        # Assert
        assert company == mock_company
        mock_company_repo.get_by_name.assert_called_once_with("Test Company")
        mock_company_repo.create.assert_called_once_with(name="Test Company")

    @pytest.mark.asyncio
    async def test_create_company_duplicate_name_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Creating company with existing name raises CompanyAlreadyExistsException."""
        # Arrange
        existing_company = Mock(spec=Company)
        mock_company_repo.get_by_name.return_value = existing_company

        # Act & Assert
        with pytest.raises(CompanyAlreadyExistsException):
            await company_service.create_company("Existing Company")

    @pytest.mark.asyncio
    async def test_get_company_success(self, company_service, mock_company_repo):
        """Get company by ID returns company."""
        # Arrange
        mock_company = Mock(spec=Company)
        mock_company.id = "123"
        mock_company_repo.get_by_id.return_value = mock_company

        # Act
        company = await company_service.get_company("123")

        # Assert
        assert company == mock_company
        mock_company_repo.get_by_id.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_get_company_not_found_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Get company with invalid ID raises CompanyNotFoundException."""
        # Arrange
        mock_company_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(CompanyNotFoundException):
            await company_service.get_company("invalid-id")

    @pytest.mark.asyncio
    async def test_list_companies(self, company_service, mock_company_repo):
        """List companies returns companies from repository."""
        # Arrange
        mock_companies = [Mock(spec=Company), Mock(spec=Company)]
        mock_company_repo.get_all.return_value = mock_companies

        # Act
        companies = await company_service.list_companies(skip=0, limit=10)

        # Assert
        assert companies == mock_companies
        mock_company_repo.get_all.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_update_company_name_success(
        self, company_service, mock_company_repo
    ):
        """Update company name succeeds."""
        # Arrange
        existing_company = Mock(spec=Company)
        existing_company.id = "123"
        existing_company.name = "Old Name"
        updated_company = Mock(spec=Company)
        updated_company.name = "New Name"

        mock_company_repo.get_by_id.return_value = existing_company
        mock_company_repo.get_by_name.return_value = None
        mock_company_repo.update.return_value = updated_company

        # Act
        company = await company_service.update_company(
            company_id="123",
            name="New Name",
        )

        # Assert
        assert company == updated_company
        mock_company_repo.get_by_name.assert_called_once_with("New Name")
        mock_company_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_company_duplicate_name_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Updating company to existing name raises exception."""
        # Arrange
        existing_company = Mock(spec=Company)
        existing_company.id = "123"
        existing_company.name = "Old Name"
        conflict_company = Mock(spec=Company)

        mock_company_repo.get_by_id.return_value = existing_company
        mock_company_repo.get_by_name.return_value = conflict_company

        # Act & Assert
        with pytest.raises(CompanyAlreadyExistsException):
            await company_service.update_company(
                company_id="123",
                name="Existing Name",
            )

    @pytest.mark.asyncio
    async def test_update_company_not_found_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Update non-existent company raises CompanyNotFoundException."""
        # Arrange
        mock_company_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(CompanyNotFoundException):
            await company_service.update_company(
                company_id="invalid-id",
                name="New Name",
            )

    @pytest.mark.asyncio
    async def test_update_company_is_active(
        self, company_service, mock_company_repo
    ):
        """Update company active status."""
        # Arrange
        existing_company = Mock(spec=Company)
        existing_company.id = "123"
        existing_company.name = "Test Company"
        updated_company = Mock(spec=Company)

        mock_company_repo.get_by_id.return_value = existing_company
        mock_company_repo.update.return_value = updated_company

        # Act
        company = await company_service.update_company(
            company_id="123",
            is_active=False,
        )

        # Assert
        assert company == updated_company
        mock_company_repo.update.assert_called_once_with(
            company_id="123",
            name=None,
            is_active=False,
        )

    @pytest.mark.asyncio
    async def test_delete_company_success(
        self, company_service, mock_company_repo
    ):
        """Delete company calls repository delete."""
        # Arrange
        mock_company = Mock(spec=Company)
        mock_company.id = "123"
        mock_company_repo.get_by_id.return_value = mock_company
        mock_company_repo.delete.return_value = True

        # Act
        await company_service.delete_company("123")

        # Assert
        mock_company_repo.delete.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_delete_company_not_found_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Delete non-existent company raises CompanyNotFoundException."""
        # Arrange
        mock_company_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(CompanyNotFoundException):
            await company_service.delete_company("invalid-id")

    @pytest.mark.asyncio
    async def test_delete_company_failure_raises_exception(
        self, company_service, mock_company_repo
    ):
        """Delete company that fails to delete raises CompanyNotFoundException."""
        # Arrange
        mock_company = Mock(spec=Company)
        mock_company.id = "123"
        mock_company_repo.get_by_id.return_value = mock_company
        mock_company_repo.delete.return_value = False

        # Act & Assert
        with pytest.raises(CompanyNotFoundException):
            await company_service.delete_company("123")
