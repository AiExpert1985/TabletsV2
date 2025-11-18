"""Business logic for company management (system admin operations)."""
from features.company.models import Company
from features.company.repository import CompanyRepository
from core.exceptions import AppException


class CompanyAlreadyExistsException(AppException):
    """Company name already exists."""

    def __init__(self, name: str) -> None:
        super().__init__(
            code="COMPANY_ALREADY_EXISTS",
            message=f"Company name '{name}' already exists"
        )


class CompanyNotFoundException(AppException):
    """Company not found."""

    def __init__(self) -> None:
        super().__init__(
            code="COMPANY_NOT_FOUND",
            message="Company not found"
        )


class CompanyService:
    """Company management service - handles business logic for company operations."""

    company_repo: CompanyRepository

    def __init__(self, company_repo: CompanyRepository) -> None:
        self.company_repo = company_repo

    async def create_company(self, name: str) -> Company:
        """
        Create a new company.

        Business rules:
        - Company name must be unique

        Args:
            name: Company name

        Returns:
            Created company

        Raises:
            CompanyAlreadyExistsException: Company name already exists
        """
        # Check if company name already exists
        existing = await self.company_repo.get_by_name(name)
        if existing:
            raise CompanyAlreadyExistsException(name)

        # Create company
        company = await self.company_repo.create(name=name)

        return company

    async def get_company(self, company_id: str) -> Company:
        """
        Get company by ID.

        Args:
            company_id: Company UUID

        Returns:
            Company

        Raises:
            CompanyNotFoundException: Company not found
        """
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise CompanyNotFoundException()
        return company

    async def list_companies(self, skip: int = 0, limit: int = 100) -> list[Company]:
        """
        Get all companies with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of companies
        """
        return await self.company_repo.get_all(skip=skip, limit=limit)

    async def update_company(
        self,
        company_id: str,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> Company:
        """
        Update company.

        Business rules:
        - New name must be unique if changed

        Args:
            company_id: Company UUID
            name: New company name (optional)
            is_active: New active status (optional)

        Returns:
            Updated company

        Raises:
            CompanyNotFoundException: Company not found
            CompanyAlreadyExistsException: New name already exists
        """
        # 1. Check if company exists
        company = await self.get_company(company_id)

        # 2. Check if new name conflicts
        if name and name != company.name:
            existing = await self.company_repo.get_by_name(name)
            if existing:
                raise CompanyAlreadyExistsException(name)

        # 3. Update company
        updated_company = await self.company_repo.update(
            company_id=company_id,
            name=name,
            is_active=is_active,
        )

        if not updated_company:
            # This should not happen if repository is working correctly
            raise CompanyNotFoundException()

        return updated_company

    async def delete_company(self, company_id: str) -> None:
        """
        Delete company.

        Business rules:
        - Deletes all associated users (cascade)

        Args:
            company_id: Company UUID

        Raises:
            CompanyNotFoundException: Company not found
        """
        # Check if company exists
        await self.get_company(company_id)

        # Delete company (cascade deletes users)
        deleted = await self.company_repo.delete(company_id)

        if not deleted:
            # This should not happen if repository is working correctly
            raise CompanyNotFoundException()
