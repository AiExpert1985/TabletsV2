"""Business logic for user management (system admin operations)."""
import uuid
from typing import TYPE_CHECKING

from features.auth.models import User, UserRole
from features.users.repository import UserRepository
from core.security import hash_password, normalize_phone_number
from core.exceptions import (
    PhoneAlreadyExistsException,
    UserNotFoundException,
)

if TYPE_CHECKING:
    from features.audit.service import AuditService


class UserService:
    """User management service - handles business logic for user CRUD operations."""

    user_repo: UserRepository
    audit_service: "AuditService | None"

    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: "AuditService | None" = None,
    ) -> None:
        self.user_repo = user_repo
        self.audit_service = audit_service

    async def create_user(
        self,
        phone_number: str,
        password: str,
        company_id: str | None,
        role: str,
        current_user: User,
        email: str | None = None,
        is_active: bool = True,
    ) -> User:
        """
        Create a new user (system admin operation).

        Business rules:
        - System admin must have company_id = None
        - Other roles must have a company_id
        - Phone numbers are unique across the system
        - Passwords are hashed with bcrypt

        Args:
            phone_number: Phone number (will be normalized)
            password: Plain text password (will be hashed)
            company_id: UUID of company (None for system admin)
            role: User role (e.g., system_admin, company_admin, accountant, viewer)
            current_user: User performing the action (for audit trail)
            email: Optional email address
            is_active: Whether user is active (default: True)

        Returns:
            Created user

        Raises:
            PhoneAlreadyExistsException: Phone number already exists
            ValueError: Invalid role/company_id combination
        """
        # 1. Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)

        # 2. Check if phone already exists
        if await self.user_repo.phone_exists(normalized_phone):
            raise PhoneAlreadyExistsException()

        # 3. Validate role and company_id combination
        user_role = UserRole(role)
        if user_role == UserRole.SYSTEM_ADMIN and company_id:
            raise ValueError("System admin cannot have a company_id")

        if user_role != UserRole.SYSTEM_ADMIN and not company_id:
            raise ValueError("Non-system-admin users must have a company_id")

        # 4. Hash password
        hashed_password = hash_password(password)

        # 5. Create user model
        user = User(
            phone_number=normalized_phone,
            hashed_password=hashed_password,
            email=email,
            company_id=uuid.UUID(company_id) if company_id else None,
            role=user_role,
            is_active=is_active,
        )

        # 6. Save to repository
        user = await self.user_repo.save(user)

        # 7. Log creation to audit trail
        if self.audit_service:
            await self.audit_service.log_create(
                user=current_user,
                entity_type="User",
                entity_id=str(user.id),
                values={
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "role": user.role.value,
                    "company_id": str(user.company_id) if user.company_id else None,
                    "is_active": user.is_active,
                },
                company_id=user.company_id,
            )

        return user

    async def get_user(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User

        Raises:
            UserNotFoundException: User not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of users
        """
        return await self.user_repo.get_all(skip, limit)

    async def update_user(
        self,
        user_id: str,
        current_user: User,
        phone_number: str | None = None,
        password: str | None = None,
        email: str | None = None,
        company_id: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        """
        Update user.

        Business rules:
        - Cannot change role to system_admin if user has company_id
        - Phone number must be unique if changed
        - Password is hashed if provided

        Args:
            user_id: User UUID
            current_user: User performing the action (for audit trail)
            phone_number: New phone number (optional)
            password: New password (optional, will be hashed)
            email: New email (optional)
            company_id: New company_id (optional)
            role: New role (optional)
            is_active: New active status (optional)

        Returns:
            Updated user

        Raises:
            UserNotFoundException: User not found
            PhoneAlreadyExistsException: New phone number already exists
            ValueError: Invalid role/company_id combination
        """
        # 1. Get existing user
        user = await self.get_user(user_id)

        # 2. Capture old values for audit trail
        old_values = {
            "phone_number": user.phone_number,
            "email": user.email,
            "role": user.role.value,
            "company_id": str(user.company_id) if user.company_id else None,
            "is_active": user.is_active,
        }

        # 3. Update password if provided
        if password:
            user.hashed_password = hash_password(password)

        # 4. Update phone if provided
        if phone_number:
            normalized_phone = normalize_phone_number(phone_number)
            if normalized_phone != user.phone_number:
                if await self.user_repo.phone_exists(normalized_phone):
                    raise PhoneAlreadyExistsException()
                user.phone_number = normalized_phone

        # 5. Update role with validation
        if role:
            new_role = UserRole(role)
            if new_role == UserRole.SYSTEM_ADMIN and user.company_id:
                raise ValueError("Cannot make user with company_id a system admin")
            user.role = new_role

        # 6. Update company_id
        if company_id is not None:
            user.company_id = uuid.UUID(company_id) if company_id else None

        # 7. Update other fields
        if email is not None:
            user.email = email
        if is_active is not None:
            user.is_active = is_active

        # 8. Save changes
        updated_user = await self.user_repo.update(user)

        # 9. Log update to audit trail
        if self.audit_service:
            new_values = {
                "phone_number": updated_user.phone_number,
                "email": updated_user.email,
                "role": updated_user.role.value,
                "company_id": str(updated_user.company_id) if updated_user.company_id else None,
                "is_active": updated_user.is_active,
            }
            await self.audit_service.log_update(
                user=current_user,
                entity_type="User",
                entity_id=str(updated_user.id),
                old_values=old_values,
                new_values=new_values,
                company_id=updated_user.company_id,
            )

        return updated_user

    async def delete_user(self, user_id: str, current_user: User) -> None:
        """
        Delete user.

        Business rules:
        - Cannot delete yourself

        Args:
            user_id: User UUID to delete
            current_user: Current user performing the action (for audit trail and self-deletion check)

        Raises:
            UserNotFoundException: User not found
            ValueError: Attempting to delete yourself
        """
        # 1. Prevent self-deletion
        if user_id == str(current_user.id):
            raise ValueError("Cannot delete yourself")

        # 2. Get user
        user = await self.get_user(user_id)

        # 3. Capture values for audit trail before deletion
        old_values = {
            "phone_number": user.phone_number,
            "email": user.email,
            "role": user.role.value,
            "company_id": str(user.company_id) if user.company_id else None,
            "is_active": user.is_active,
        }

        # 4. Delete
        await self.user_repo.delete(user)

        # 5. Log deletion to audit trail
        if self.audit_service:
            await self.audit_service.log_delete(
                user=current_user,
                entity_type="User",
                entity_id=user_id,
                old_values=old_values,
                company_id=user.company_id,
            )
