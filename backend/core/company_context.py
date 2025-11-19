"""
Company context for multi-tenant data isolation.

Provides automatic company-based filtering for all queries.
System admin can access all companies' data.
"""
from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from features.auth.dependencies import CurrentUser
from core.enums import UserRole
from features.logging.logger import get_logger

logger = get_logger(__name__)


class CompanyContext:
    """
    Company context for data isolation.

    Encapsulates company filtering logic:
    - Regular users: filtered to their company only
    - System admin: can access all companies

    Usage in repositories:
        async def get_products(self, company_ctx: CompanyContext):
            query = select(Product)
            if company_ctx.should_filter:
                query = query.where(Product.company_id == company_ctx.company_id)
            return await self.db.execute(query)
    """

    def __init__(self, user: CurrentUser):
        """
        Initialize company context from current user.

        Args:
            user: Currently authenticated user
        """
        self.user = user
        self.company_id: UUID | None = user.company_id
        self.is_system_admin: bool = (user.role == UserRole.SYSTEM_ADMIN)

        # System admin has no company_id but can access all data
        # Regular users must have a company_id
        if not self.is_system_admin and self.company_id is None:
            logger.error(
                f"User {user.id} has no company_id and is not system admin. "
                "This should not happen - data indicates corruption."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User account configuration error. Contact administrator."
            )

    @property
    def should_filter(self) -> bool:
        """
        Whether queries should be filtered by company.

        Returns:
            True if filtering required (regular users)
            False if no filtering (system admin)
        """
        return not self.is_system_admin

    def filter_query_by_company(self, query, model_class):
        """
        Apply company filtering to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            model_class: Model class with company_id field

        Returns:
            Filtered query (if needed) or original query

        Example:
            query = select(Product)
            query = company_ctx.filter_query_by_company(query, Product)
        """
        if self.should_filter:
            # Regular user - filter to their company only
            return query.where(model_class.company_id == self.company_id)
        else:
            # System admin - no filtering, return all
            return query

    def ensure_company_access(self, resource_company_id: UUID | None) -> None:
        """
        Verify user has access to a specific company's resource.

        Raises 403 if user tries to access another company's data.

        Args:
            resource_company_id: The company_id of the resource being accessed

        Raises:
            HTTPException: 403 if access denied

        Example:
            # When updating a product
            product = await repo.get_by_id(product_id)
            company_ctx.ensure_company_access(product.company_id)
        """
        # System admin can access any company
        if self.is_system_admin:
            return

        # Regular user - must match their company
        if resource_company_id != self.company_id:
            logger.warning(
                f"User {self.user.id} (company={self.company_id}) attempted to access "
                f"resource from company={resource_company_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )

    def get_company_id_for_create(self) -> UUID:
        """
        Get company_id to use when creating new resources.

        Returns:
            company_id for the new resource

        Raises:
            HTTPException: 400 if system admin doesn't specify company_id

        Example:
            # Creating a new product
            product = Product(
                name=request.name,
                company_id=company_ctx.get_company_id_for_create(),
                ...
            )

        Note:
            System admin should explicitly pass company_id in request body.
            Regular users automatically use their own company_id.
        """
        if self.company_id is None:
            # System admin creating resource - should specify company in request
            logger.error(
                f"System admin {self.user.id} attempted to create resource "
                "without specifying company_id"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System admin must specify company_id when creating resources"
            )

        return self.company_id

    def __repr__(self) -> str:
        """String representation for debugging."""
        if self.is_system_admin:
            return f"<CompanyContext: SYSTEM_ADMIN (no filtering)>"
        return f"<CompanyContext: company_id={self.company_id}>"


def get_company_context(current_user: CurrentUser) -> CompanyContext:
    """
    FastAPI dependency to get company context.

    Args:
        current_user: Currently authenticated user (injected)

    Returns:
        CompanyContext instance

    Usage:
        @router.get("/products")
        async def get_products(
            company_ctx: Annotated[CompanyContext, Depends(get_company_context)]
        ):
            # company_ctx is automatically populated
            ...
    """
    return CompanyContext(user=current_user)


# Type alias for convenience
CompanyCtx = Annotated[CompanyContext, Depends(get_company_context)]
