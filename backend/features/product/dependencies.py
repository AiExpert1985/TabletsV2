"""FastAPI dependencies for product feature."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from features.product.repository import ProductRepository
from features.product.service import ProductService


def get_product_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProductService:
    """Get product service dependency."""
    product_repo = ProductRepository(db)
    return ProductService(product_repo)
