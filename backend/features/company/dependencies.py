"""FastAPI dependencies for company feature."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from features.company.repository import CompanyRepository
from features.company.service import CompanyService
from features.audit.service import AuditService
from features.audit.dependencies import get_audit_service


def get_company_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)]
) -> CompanyService:
    """Get company service."""
    company_repo = CompanyRepository(db)
    return CompanyService(company_repo, audit_service)
