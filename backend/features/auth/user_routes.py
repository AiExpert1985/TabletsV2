"""User management routes - System Admin only."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from features.auth.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
)
from features.auth.models import User, UserRole
from features.auth.repository import UserRepository
from features.auth.dependencies import CurrentUser
from features.auth.services import hash_password
from features.auth.routes import build_user_response
from core.database import get_db


router = APIRouter(prefix="/users", tags=["User Management"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


async def require_system_admin(current_user: CurrentUser) -> None:
    """Require system admin role."""
    if current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system admin can access user management"
        )


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=list[UserResponse])
async def get_users(
    _: Annotated[None, Depends(require_system_admin)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """
    Get all users (system admin only).

    System admin can see all users across all companies.
    """
    users = await user_repo.get_all(skip, limit)
    return [build_user_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: Annotated[None, Depends(require_system_admin)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
):
    """Get user by ID (system admin only)."""
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return build_user_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    _: Annotated[None, Depends(require_system_admin)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
):
    """
    Create a new user (system admin only).

    - For regular users and company admins, company_id is required
    - For system admin, company_id must be None
    - Password is permanent (no forced change on first login)
    """
    # Validate phone number uniqueness
    if await user_repo.phone_exists(request.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already exists"
        )

    # Validate role and company_id combination
    if request.role == "system_admin" and request.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System admin cannot have a company_id"
        )

    if request.role in ["user", "company_admin"] and not request.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Regular users and company admins must have a company_id"
        )

    # Hash password
    hashed_password = hash_password(request.password)

    # Create user
    user = User(
        phone_number=request.phone_number,
        hashed_password=hashed_password,
        email=request.email,
        company_id=uuid.UUID(request.company_id) if request.company_id else None,
        role=UserRole(request.role),
        company_roles=request.company_roles,
        is_active=request.is_active
    )

    user_repo.db.add(user)
    await user_repo.db.flush()
    await user_repo.db.refresh(user)
    await user_repo.db.commit()

    return build_user_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    _: Annotated[None, Depends(require_system_admin)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
):
    """Update user (system admin only)."""
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields (only provided fields)
    update_data = request.model_dump(exclude_unset=True)

    # Special handling for password
    if "password" in update_data:
        user.hashed_password = hash_password(update_data["password"])
        del update_data["password"]

    # Special handling for role and company_id
    if "role" in update_data:
        new_role = UserRole(update_data["role"])
        if new_role == UserRole.SYSTEM_ADMIN and user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot make user with company_id a system admin"
            )
        user.role = new_role
        del update_data["role"]

    if "company_id" in update_data:
        if update_data["company_id"]:
            user.company_id = uuid.UUID(update_data["company_id"])
        else:
            user.company_id = None
        del update_data["company_id"]

    # Update remaining fields
    for field, value in update_data.items():
        setattr(user, field, value)

    user = await user_repo.update(user)
    await user_repo.db.commit()

    return build_user_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_system_admin)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
):
    """Delete user (system admin only)."""
    # Prevent deleting yourself
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await user_repo.delete(user)
    await user_repo.db.commit()
