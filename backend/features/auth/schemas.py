"""Pydantic schemas (DTOs) for API request/response."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "PHONE_ALREADY_EXISTS",
                    "message": "Phone number already registered",
                }
            }
        }
    )
