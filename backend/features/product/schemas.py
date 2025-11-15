"""
Product request/response schemas.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ProductCreateRequest(BaseModel):
    """Request to create a new product."""
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    cost_price: Decimal = Field(..., ge=0, decimal_places=2)
    selling_price: Decimal = Field(..., ge=0, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    company_id: UUID | None = None  # Only for system admin

    @field_validator('name', 'sku')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()


class ProductUpdateRequest(BaseModel):
    """Request to update existing product."""
    name: str | None = Field(None, min_length=1, max_length=255)
    sku: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    cost_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    selling_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    stock_quantity: int | None = Field(None, ge=0)
    reorder_level: int | None = Field(None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Product response."""
    id: UUID
    company_id: UUID
    name: str
    sku: str
    description: str | None
    cost_price: Decimal
    selling_price: Decimal
    stock_quantity: int
    reorder_level: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
