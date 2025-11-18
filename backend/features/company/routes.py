"""FastAPI routes for company management (system admin only)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from features.authorization.dependencies import require_permission
from features.authorization.permissions import Permission
from features.company.schemas import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
)
from features.company.dependencies import get_company_service
from features.company.service import CompanyService, CompanyAlreadyExistsException, CompanyNotFoundException
from features.auth.schemas import MessageResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreateRequest,
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    _: Annotated[None, Depends(require_permission(Permission.CREATE_COMPANIES))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create new company (system admin only).

    - **name**: Company name (unique)
    """
    try:
        company = await company_service.create_company(name=request.name)
        await db.commit()

        return CompanyResponse(
            id=str(company.id),
            name=company.name,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    except CompanyAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )


@router.get("", response_model=list[CompanyResponse])
async def get_companies(
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_COMPANIES))],
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all companies (system admin only).

    Supports pagination with skip/limit.
    """
    companies = await company_service.list_companies(skip=skip, limit=limit)

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
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_COMPANIES))],
):
    """
    Get company by ID (system admin only).
    """
    try:
        company = await company_service.get_company(company_id)

        return CompanyResponse(
            id=str(company.id),
            name=company.name,
            is_active=company.is_active,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    except CompanyNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    _: Annotated[None, Depends(require_permission(Permission.EDIT_COMPANIES))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update company (system admin only).

    Can update:
    - **name**: Company name
    - **is_active**: Active status
    """
    try:
        updated_company = await company_service.update_company(
            company_id=company_id,
            name=request.name,
            is_active=request.is_active,
        )

        await db.commit()

        return CompanyResponse(
            id=str(updated_company.id),
            name=updated_company.name,
            is_active=updated_company.is_active,
            created_at=updated_company.created_at,
            updated_at=updated_company.updated_at,
        )

    except CompanyNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    except CompanyAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )


@router.delete("/{company_id}", response_model=MessageResponse)
async def delete_company(
    company_id: str,
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    _: Annotated[None, Depends(require_permission(Permission.DELETE_COMPANIES))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete company (system admin only).

    WARNING: This will also delete all users belonging to this company (cascade delete).
    """
    try:
        # Get company name before deleting
        company = await company_service.get_company(company_id)
        company_name = company.name

        # Delete company
        await company_service.delete_company(company_id)
        await db.commit()

        return MessageResponse(message=f"Company '{company_name}' deleted successfully")

    except CompanyNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
