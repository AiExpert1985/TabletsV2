"""User management routes - System Admin only."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from features.users.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
)
from features.users.service import UserService
from features.users.dependencies import (
    get_user_service,
    require_system_admin,
    build_user_response,
)
from features.auth.dependencies import CurrentUser
from core.database import get_db
from core.exceptions import (
    PhoneAlreadyExistsException,
    UserNotFoundException,
)


router = APIRouter(prefix="/users", tags=["User Management"])


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=list[UserResponse])
async def get_users(
    _: Annotated[None, Depends(require_system_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return")
):
    """
    Get all users (system admin only).

    System admin can see all users across all companies.
    """
    users = await user_service.list_users(skip, limit)
    return [build_user_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: Annotated[None, Depends(require_system_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """Get user by ID (system admin only)."""
    try:
        user = await user_service.get_user(user_id)
        return build_user_response(user)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_system_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new user (system admin only).

    - For regular users and company admins, company_id is required
    - For system admin, company_id must be None
    - Password is permanent (no forced change on first login)
    """
    try:
        user = await user_service.create_user(
            phone_number=request.phone_number,
            password=request.password,
            company_id=request.company_id,
            role=request.role,
            current_user=current_user,
            email=request.email,
            is_active=request.is_active,
        )

        await db.commit()
        return build_user_response(user)

    except PhoneAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_system_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update user (system admin only)."""
    try:
        # Get only provided fields
        update_data = request.model_dump(exclude_unset=True)

        user = await user_service.update_user(
            user_id=user_id,
            current_user=current_user,
            phone_number=update_data.get("phone_number"),
            password=update_data.get("password"),
            email=update_data.get("email"),
            company_id=update_data.get("company_id"),
            role=update_data.get("role"),
            is_active=update_data.get("is_active"),
        )

        await db.commit()
        return build_user_response(user)

    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except PhoneAlreadyExistsException as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser,
    _: Annotated[None, Depends(require_system_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete user (system admin only)."""
    try:
        await user_service.delete_user(user_id, current_user)
        await db.commit()

    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
