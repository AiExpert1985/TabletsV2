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
from features.product.schemas import ProductCreateRequest, ProductUpdateRequest, ProductResponse
from features.product.models import Product
from features.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


def get_product_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProductRepository:
    """Get product repository dependency."""
    return ProductRepository(db)


@router.get("", response_model=list[ProductResponse])
async def get_products(
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
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

    products = await product_repo.get_all_for_company(company_ctx, skip, limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/search", response_model=list[ProductResponse])
async def search_products(
    search: str,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
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
    products = await product_repo.search_products(search, company_ctx, skip, limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/low-stock", response_model=list[ProductResponse])
async def get_low_stock_products(
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_PRODUCTS))]
):
    """
    Get products below reorder level within user's company.

    Useful for warehouse management alerts.
    """
    products = await product_repo.get_low_stock_products(company_ctx)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
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
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
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
    # Determine company_id
    if company_ctx.is_system_admin:
        # System admin must explicitly specify company
        if not request.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System admin must specify company_id when creating products"
            )
        company_id = request.company_id
        logger.info(f"System admin creating product for company {company_id}")
    else:
        # Regular user - use their company
        company_id = company_ctx.company_id
        logger.info(f"User {company_ctx.user.id} creating product for their company")

    # Check for duplicate SKU within the company
    existing = await product_repo.get_by_sku(request.sku, company_ctx)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{request.sku}' already exists"
        )

    # Create product
    product = Product(
        company_id=company_id,
        name=request.name,
        sku=request.sku,
        description=request.description,
        cost_price=request.cost_price,
        selling_price=request.selling_price,
        stock_quantity=request.stock_quantity,
        reorder_level=request.reorder_level,
    )

    product = await product_repo.create(product)

    logger.info(f"Created product {product.id} for company {company_id}")
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
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
    # Get product with company access check
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check SKU uniqueness if changing
    if request.sku and request.sku != product.sku:
        existing = await product_repo.get_by_sku(request.sku, company_ctx)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{request.sku}' already exists"
            )

    # Update fields (only if provided)
    if request.name is not None:
        product.name = request.name
    if request.sku is not None:
        product.sku = request.sku
    if request.description is not None:
        product.description = request.description
    if request.cost_price is not None:
        product.cost_price = request.cost_price
    if request.selling_price is not None:
        product.selling_price = request.selling_price
    if request.stock_quantity is not None:
        product.stock_quantity = request.stock_quantity
    if request.reorder_level is not None:
        product.reorder_level = request.reorder_level
    if request.is_active is not None:
        product.is_active = request.is_active

    product = await product_repo.update(product)

    logger.info(f"Updated product {product.id}")
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    company_ctx: CompanyCtx,
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    _: Annotated[None, Depends(require_permission(Permission.DELETE_PRODUCTS))]
):
    """
    Delete a product.

    Automatically verifies company access before deleting.

    Returns:
        - 204: Product deleted successfully
        - 404: Product not found OR belongs to different company
    """
    # Get product with company access check
    product = await product_repo.get_by_id_for_company(product_id, company_ctx)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await product_repo.delete(product)

    logger.info(f"Deleted product {product_id}")
    return None
