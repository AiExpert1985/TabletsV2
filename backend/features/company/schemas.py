"""Pydantic schemas for Company feature."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Request Schemas
# ============================================================================

class CompanyCreateRequest(BaseModel):
    """Create company request."""
    name: str = Field(..., min_length=1, max_length=255)


class CompanyUpdateRequest(BaseModel):
    """Update company request."""
    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None


# ============================================================================
# Response Schemas
# ============================================================================

class CompanyResponse(BaseModel):
    """Company response."""
    id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
