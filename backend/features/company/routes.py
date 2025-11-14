"""FastAPI routes for company management (system admin only)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.authorization import require_system_admin
from features.auth.dependencies import CurrentUser
from features.company.schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
)
from features.company.repository import CompanyRepository
from features.auth.schemas import MessageResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


def get_company_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> CompanyRepository:
    """Get company repository."""
    return CompanyRepository(db)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreateRequest,
    current_user: CurrentUser,
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
):
    """
    Create new company (system admin only).

    - **name**: Company name (unique)
    """
    # Check authorization
    require_system_admin(current_user)

    # Check if company name already exists
    existing = await company_repo.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company name already exists"
        )

    # Create company
    company = await company_repo.create(name=request.name)

    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        is_active=company.is_active,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


@router.get("", response_model=list[CompanyResponse])
async def get_companies(
    current_user: CurrentUser,
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all companies (system admin only).

    Supports pagination with skip/limit.
    """
    # Check authorization
    require_system_admin(current_user)

    companies = await company_repo.get_all(skip=skip, limit=limit)

    return [
        CompanyResponse(
            id=str(c.id),
            name=c.name,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in companies
    ]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    current_user: CurrentUser,
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
):
    """
    Get company by ID (system admin only).
    """
    # Check authorization
    require_system_admin(current_user)

    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        is_active=company.is_active,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    current_user: CurrentUser,
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
):
    """
    Update company (system admin only).

    Can update:
    - **name**: Company name
    - **is_active**: Active status
    """
    # Check authorization
    require_system_admin(current_user)

    # Check if company exists
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Check if new name conflicts
    if request.name and request.name != company.name:
        existing = await company_repo.get_by_name(request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company name already exists"
            )

    # Update company
    updated_company = await company_repo.update(
        company_id=company_id,
        name=request.name,
        is_active=request.is_active,
    )

    if not updated_company:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )

    return CompanyResponse(
        id=str(updated_company.id),
        name=updated_company.name,
        is_active=updated_company.is_active,
        created_at=updated_company.created_at,
        updated_at=updated_company.updated_at,
    )


@router.delete("/{company_id}", response_model=MessageResponse)
async def delete_company(
    company_id: str,
    current_user: CurrentUser,
    company_repo: Annotated[CompanyRepository, Depends(get_company_repository)],
):
    """
    Delete company (system admin only).

    WARNING: This will also delete all users belonging to this company (cascade delete).
    """
    # Check authorization
    require_system_admin(current_user)

    # Check if company exists
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Delete company
    deleted = await company_repo.delete(company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )

    return MessageResponse(message=f"Company '{company.name}' deleted successfully")
