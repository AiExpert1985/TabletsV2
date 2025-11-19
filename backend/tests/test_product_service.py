"""Tests for ProductService - product management business logic."""
import pytest
from unittest.mock import AsyncMock, Mock
from decimal import Decimal
from uuid import uuid4
from features.product.service import ProductService, ProductAlreadyExistsException, ProductNotFoundException
from features.product.models import Product
from core.company_context import CompanyContext
from features.users.models import User
from core.enums import UserRole


@pytest.fixture
def mock_product_repo():
    """Create mock product repository."""
    repo = Mock()
    repo.get_by_sku = AsyncMock(return_value=None)
    repo.get_by_id_for_company = AsyncMock()
    repo.get_all_for_company = AsyncMock()
    repo.search_products = AsyncMock()
    repo.get_low_stock_products = AsyncMock()
    repo.create = AsyncMock()
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
def product_service(mock_product_repo, mock_audit_service):
    """Create ProductService with mocked repository and audit service."""
    return ProductService(mock_product_repo, mock_audit_service)


@pytest.fixture
def company_ctx_regular():
    """Create company context for regular user."""
    user = User(
        id=uuid4(),
        name="Test User",
        phone_number="+9647700000001",
        hashed_password="hashed",
        company_id=uuid4(),
        role=UserRole.VIEWER,
        is_active=True,
    )
    return CompanyContext(user=user)


@pytest.fixture
def company_ctx_admin():
    """Create company context for system admin."""
    user = User(
        id=uuid4(),
        name="Test User",
        phone_number="+9647700000001",
        hashed_password="hashed",
        role=UserRole.SYSTEM_ADMIN,
        is_active=True,
    )
    return CompanyContext(user=user)


class TestProductService:
    """Test ProductService business logic."""

    @pytest.mark.asyncio
    async def test_create_product_regular_user_success(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Regular user can create product for their company."""
        # Arrange
        mock_product = Mock(spec=Product)
        mock_product_repo.create.return_value = mock_product

        # Act
        product = await product_service.create_product(
            company_ctx=company_ctx_regular,
            name="Test Product",
            sku="SKU001",
            selling_price=Decimal("100.00"),
        )

        # Assert
        assert product == mock_product
        assert mock_product_repo.get_by_sku.called
        assert mock_product_repo.create.called

    @pytest.mark.asyncio
    async def test_create_product_system_admin_without_company_id_raises_error(
        self, product_service, mock_product_repo, company_ctx_admin
    ):
        """System admin must specify company_id."""
        # Act & Assert
        with pytest.raises(ValueError, match="System admin must specify company_id"):
            await product_service.create_product(
                company_ctx=company_ctx_admin,
                name="Test Product",
                sku="SKU001",
                selling_price=Decimal("100.00"),
                company_id=None,
            )

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku_raises_exception(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Creating product with existing SKU raises ProductAlreadyExistsException."""
        # Arrange
        existing_product = Mock(spec=Product)
        mock_product_repo.get_by_sku.return_value = existing_product

        # Act & Assert
        with pytest.raises(ProductAlreadyExistsException):
            await product_service.create_product(
                company_ctx=company_ctx_regular,
                name="Test Product",
                sku="SKU001",
                selling_price=Decimal("100.00"),
            )

    @pytest.mark.asyncio
    async def test_get_product_success(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Get product returns product from repository."""
        # Arrange
        product_id = uuid4()
        mock_product = Mock(spec=Product)
        mock_product_repo.get_by_id_for_company.return_value = mock_product

        # Act
        product = await product_service.get_product(product_id, company_ctx_regular)

        # Assert
        assert product == mock_product
        mock_product_repo.get_by_id_for_company.assert_called_once_with(
            product_id, company_ctx_regular
        )

    @pytest.mark.asyncio
    async def test_get_product_not_found_raises_exception(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Get product with invalid ID raises ProductNotFoundException."""
        # Arrange
        product_id = uuid4()
        mock_product_repo.get_by_id_for_company.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundException):
            await product_service.get_product(product_id, company_ctx_regular)

    @pytest.mark.asyncio
    async def test_list_products(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """List products returns products from repository."""
        # Arrange
        mock_products = [Mock(spec=Product), Mock(spec=Product)]
        mock_product_repo.get_all_for_company.return_value = mock_products

        # Act
        products = await product_service.list_products(company_ctx_regular, skip=0, limit=10)

        # Assert
        assert products == mock_products
        mock_product_repo.get_all_for_company.assert_called_once_with(
            company_ctx_regular, 0, 10
        )

    @pytest.mark.asyncio
    async def test_search_products(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Search products calls repository search."""
        # Arrange
        mock_products = [Mock(spec=Product)]
        mock_product_repo.search_products.return_value = mock_products

        # Act
        products = await product_service.search_products(
            "test", company_ctx_regular, skip=0, limit=10
        )

        # Assert
        assert products == mock_products
        mock_product_repo.search_products.assert_called_once_with(
            "test", company_ctx_regular, 0, 10
        )

    @pytest.mark.asyncio
    async def test_get_low_stock_products(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Get low stock products calls repository."""
        # Arrange
        mock_products = [Mock(spec=Product)]
        mock_product_repo.get_low_stock_products.return_value = mock_products

        # Act
        products = await product_service.get_low_stock_products(company_ctx_regular)

        # Assert
        assert products == mock_products
        mock_product_repo.get_low_stock_products.assert_called_once_with(company_ctx_regular)

    @pytest.mark.asyncio
    async def test_update_product_success(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Update product updates fields and saves."""
        # Arrange
        product_id = uuid4()
        mock_product = Mock(spec=Product)
        mock_product.sku = "SKU001"
        mock_product_repo.get_by_id_for_company.return_value = mock_product
        mock_product_repo.update.return_value = mock_product

        # Act
        product = await product_service.update_product(
            product_id=product_id,
            company_ctx=company_ctx_regular,
            name="Updated Name",
            selling_price=Decimal("200.00"),
        )

        # Assert
        assert product.name == "Updated Name"
        assert product.selling_price == Decimal("200.00")
        mock_product_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_duplicate_sku_raises_exception(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Updating product SKU to existing SKU raises exception."""
        # Arrange
        product_id = uuid4()
        mock_product = Mock(spec=Product)
        mock_product.sku = "SKU001"
        existing_product = Mock(spec=Product)
        mock_product_repo.get_by_id_for_company.return_value = mock_product
        mock_product_repo.get_by_sku.return_value = existing_product

        # Act & Assert
        with pytest.raises(ProductAlreadyExistsException):
            await product_service.update_product(
                product_id=product_id,
                company_ctx=company_ctx_regular,
                sku="SKU002",
            )

    @pytest.mark.asyncio
    async def test_delete_product_success(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Delete product calls repository delete."""
        # Arrange
        product_id = uuid4()
        mock_product = Mock(spec=Product)
        mock_product_repo.get_by_id_for_company.return_value = mock_product

        # Act
        await product_service.delete_product(product_id, company_ctx_regular)

        # Assert
        mock_product_repo.delete.assert_called_once_with(mock_product)

    @pytest.mark.asyncio
    async def test_delete_product_not_found_raises_exception(
        self, product_service, mock_product_repo, company_ctx_regular
    ):
        """Delete non-existent product raises ProductNotFoundException."""
        # Arrange
        product_id = uuid4()
        mock_product_repo.get_by_id_for_company.return_value = None

        # Act & Assert
        with pytest.raises(ProductNotFoundException):
            await product_service.delete_product(product_id, company_ctx_regular)
