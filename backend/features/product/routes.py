"""
Product API routes demonstrating company data isolation.

This is a complete example showing all CRUD operations with
automatic company filtering.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.company_context import CompanyCtx
from features.authorization.permissions import Permission
from features.authorization.dependencies import require_permission
from features.product.repository import ProductRepository
from features.product.service import ProductService, ProductAlreadyExistsException, ProductNotFoundException
from features.product.schemas import ProductCreateRequest, ProductUpdateRequest, ProductResponse
from features.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProductService:
    """Get product service dependency."""
    product_repo = ProductRepository(db)
    return ProductService(product_repo)


@router.get("", response_model=list[ProductResponse])
async def get_products(
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all products for the user's company (with pagination).

    - Regular users: See only their company's products
    - System admin: See all products from all companies

    Query params:
        - skip: Number of records to skip (default: 0)
        - limit: Maximum number of records (default: 100, max: 1000)
    """
    logger.info(
        f"User {company_ctx.user.id} listing products "
        f"(company_filter={'ON' if company_ctx.should_filter else 'OFF'})"
    )

    products = await product_service.list_products(company_ctx, skip, limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/search", response_model=list[ProductResponse])
async def search_products(
    search: str,
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Search products by name within user's company.

    Query params:
        - search: Search term to match against product names
        - skip: Pagination offset
        - limit: Pagination limit
    """
    products = await product_service.search_products(search, company_ctx, skip, limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/low-stock", response_model=list[ProductResponse])
async def get_low_stock_products(
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))]
):
    """
    Get products below reorder level within user's company.

    Useful for warehouse management alerts.
    """
    products = await product_service.get_low_stock_products(company_ctx)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))]
):
    """
    Get product by ID.

    Automatically verifies:
    - Regular users: Can only access their company's products
    - System admin: Can access any company's products

    Returns:
        - 200: Product found and accessible
        - 404: Product not found OR belongs to different company
              (Same 404 for security - no company enumeration)
    """
    try:
        product = await product_service.get_product(product_id, company_ctx)
        return ProductResponse.model_validate(product)
    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.CREATE_PRODUCTS))]
):
    """
    Create a new product.

    **For regular users:**
    - Product automatically belongs to their company
    - company_id in request body is ignored

    **For system admin:**
    - Must specify company_id in request body
    - Creates product for specified company

    Returns:
        - 201: Product created successfully
        - 400: Invalid input or system admin didn't specify company_id
        - 409: SKU already exists in the company
    """
    try:
        # Log action
        if company_ctx.is_system_admin:
            logger.info(f"System admin creating product for company {request.company_id}")
        else:
            logger.info(f"User {company_ctx.user.id} creating product for their company")

        product = await product_service.create_product(
            company_ctx=company_ctx,
            name=request.name,
            sku=request.sku,
            selling_price=request.selling_price,
            description=request.description,
            cost_price=request.cost_price,
            stock_quantity=request.stock_quantity,
            reorder_level=request.reorder_level,
            company_id=request.company_id,
        )

        logger.info(f"Created product {product.id} for company {product.company_id}")
        return ProductResponse.model_validate(product)

    except ProductAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.EDIT_PRODUCTS))]
):
    """
    Update existing product.

    Automatically verifies company access before updating.

    Returns:
        - 200: Product updated successfully
        - 404: Product not found OR belongs to different company
        - 409: Updated SKU conflicts with another product
    """
    try:
        product = await product_service.update_product(
            product_id=product_id,
            company_ctx=company_ctx,
            name=request.name,
            sku=request.sku,
            description=request.description,
            cost_price=request.cost_price,
            selling_price=request.selling_price,
            stock_quantity=request.stock_quantity,
            reorder_level=request.reorder_level,
            is_active=request.is_active,
        )

        logger.info(f"Updated product {product.id}")
        return ProductResponse.model_validate(product)

    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    except ProductAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_service: Annotated[ProductService, Depends(get_product_service)],
    _: Annotated[None, Depends(require_permission(Permission.DELETE_PRODUCTS))]
):
    """
    Delete a product.

    Automatically verifies company access before deleting.

    Returns:
        - 204: Product deleted successfully
        - 404: Product not found OR belongs to different company
    """
    try:
        await product_service.delete_product(product_id, company_ctx)
        logger.info(f"Deleted product {product_id}")
        return None

    except ProductNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
