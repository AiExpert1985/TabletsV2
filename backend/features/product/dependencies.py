"""FastAPI dependencies for product feature."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from features.product.repository import ProductRepository
from features.product.service import ProductService
from features.audit.service import AuditService
from features.audit.dependencies import get_audit_service


def get_product_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)]
) -> ProductService:
    """Get product service dependency."""
    product_repo = ProductRepository(db)
    return ProductService(product_repo, audit_service)
