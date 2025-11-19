"""Business logic for company management (system admin operations)."""
from typing import TYPE_CHECKING
from features.company.models import Company
from features.company.repository import CompanyRepository
from core.exceptions import AppException
from core.enums import EntityType

if TYPE_CHECKING:
    from features.audit_logs.service import AuditService
    from features.users.models import User


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
    audit_service: "AuditService"

    def __init__(
        self,
        company_repo: CompanyRepository,
        audit_service: "AuditService"
    ) -> None:
        self.company_repo = company_repo
        self.audit_service = audit_service

    async def create_company(self, name: str, current_user: "User") -> Company:
        """
        Create a new company.

        Business rules:
        - Company name must be unique

        Args:
            name: Company name
            current_user: User performing the creation (for audit logging)

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

        # Log creation
        await self.audit_service.log_create(
            user=current_user,
            entity_type=EntityType.COMPANY,
            entity_id=str(company.id),
            values={
                "id": str(company.id),
                "name": company.name,
                "is_active": company.is_active,
            },
            company_id=None  # Company management is system admin only
        )

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
        current_user: "User",
        name: str | None = None,
        is_active: bool | None = None,
    ) -> Company:
        """
        Update company.

        Business rules:
        - New name must be unique if changed

        Args:
            company_id: Company UUID
            current_user: User performing the update (for audit logging)
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

        # 2. Capture old values for audit logging
        old_values = {
            "id": str(company.id),
            "name": company.name,
            "is_active": company.is_active,
        }

        # 3. Check if new name conflicts
        if name and name != company.name:
            existing = await self.company_repo.get_by_name(name)
            if existing:
                raise CompanyAlreadyExistsException(name)

        # 4. Update company
        updated_company = await self.company_repo.update(
            company_id=company_id,
            name=name,
            is_active=is_active,
        )

        if not updated_company:
            # This should not happen if repository is working correctly
            raise CompanyNotFoundException()

        # 5. Log update with old and new values
        await self.audit_service.log_update(
            user=current_user,
            entity_type=EntityType.COMPANY,
            entity_id=str(updated_company.id),
            old_values=old_values,
            new_values={
                "id": str(updated_company.id),
                "name": updated_company.name,
                "is_active": updated_company.is_active,
            },
            company_id=None  # Company management is system admin only
        )

        return updated_company

    async def delete_company(self, company_id: str, current_user: "User") -> None:
        """
        Delete company.

        Business rules:
        - Deletes all associated users (cascade)

        Args:
            company_id: Company UUID
            current_user: User performing the deletion (for audit logging)

        Raises:
            CompanyNotFoundException: Company not found
        """
        # Check if company exists
        company = await self.get_company(company_id)

        # Capture old values for audit logging
        old_values = {
            "id": str(company.id),
            "name": company.name,
            "is_active": company.is_active,
        }

        # Delete company (cascade deletes users)
        deleted = await self.company_repo.delete(company_id)

        if not deleted:
            # This should not happen if repository is working correctly
            raise CompanyNotFoundException()

        # Log deletion
        await self.audit_service.log_delete(
            user=current_user,
            entity_type=EntityType.COMPANY,
            entity_id=str(company.id),
            values=old_values,
            company_id=None  # Company management is system admin only
        )
