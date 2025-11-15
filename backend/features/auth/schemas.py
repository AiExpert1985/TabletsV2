"""Pydantic schemas (DTOs) for API request/response."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class SignupRequest(BaseModel):
    """Signup request."""

    phone_number: str
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate passwords match."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class LoginRequest(BaseModel):
    """Login request."""

    phone_number: str
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., min_length=1)


# ============================================================================
# Response Schemas
# ============================================================================

class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response."""

    id: str
    phone_number: str
    email: str | None = None
    company_id: str | None = None  # NULL for system_admin
    role: str  # "system_admin", "company_admin", or "user"
    company_roles: list[str] = []  # List of company roles for granular permissions
    permissions: list[str] = []  # List of aggregated permissions
    is_active: bool
    is_phone_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class SignupResponse(BaseModel):
    """Signup response."""

    user: UserResponse
    tokens: TokenResponse


class LoginResponse(BaseModel):
    """Login response."""

    user: UserResponse
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "PHONE_ALREADY_EXISTS",
                    "message": "Phone number already registered",
                }
            }
        }


# ============================================================================
# User Management Schemas (System Admin Only)
# ============================================================================

class UserCreateRequest(BaseModel):
    """Create user request (system admin only)."""

    phone_number: str
    password: str = Field(..., min_length=8, max_length=128)
    email: str | None = None
    company_id: str | None = None  # Required for non-system-admin users
    role: str = "user"  # user, company_admin, system_admin
    company_roles: list[str] = []  # e.g., ["accountant", "sales"]
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Update user request (system admin only)."""

    phone_number: str | None = None
    email: str | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
    company_id: str | None = None
    role: str | None = None
    company_roles: list[str] | None = None
    is_active: bool | None = None
