"""Pydantic schemas (DTOs) for user management API."""
from pydantic import BaseModel, Field

# Re-export UserResponse from auth (shared schema)
from features.auth.schemas import UserResponse

__all__ = ["UserResponse", "UserCreateRequest", "UserUpdateRequest"]


# ============================================================================
# User Management Schemas (System Admin Only)
# ============================================================================

class UserCreateRequest(BaseModel):
    """Create user request (system admin only)."""

    phone_number: str
    password: str = Field(..., min_length=8, max_length=128)
    email: str | None = None
    company_id: str | None = None  # Required for non-system-admin users
    role: str = "viewer"  # Role: system_admin, company_admin, accountant, etc.
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Update user request (system admin only)."""

    phone_number: str | None = None
    email: str | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
    company_id: str | None = None
    role: str | None = None  # Update user's role
    is_active: bool | None = None
