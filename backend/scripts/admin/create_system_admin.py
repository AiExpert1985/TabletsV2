#!/usr/bin/env python3
"""Script to create a system admin user in the database.

Usage:
    cd backend
    python scripts/admin/create_system_admin.py

This script creates a system admin user interactively with proper validation.
Use this for initial setup or to create additional system admins.
"""
import asyncio
import sys
from pathlib import Path
from getpass import getpass

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from core.database import AsyncSessionLocal, init_db
from core.security import (
    hash_password,
    validate_password_strength,
    normalize_phone_number
)
from features.auth.repository import UserRepository
from features.auth.models import UserRole
from core.exceptions import PhoneAlreadyExistsException


async def create_system_admin(
    phone_number: str,
    password: str,
    email: str | None = None
) -> int:
    """Create a system admin user.

    Args:
        phone_number: Phone number for the admin (will be normalized)
        password: Password for the admin (will be validated)
        email: Optional email address

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Initialize database (create tables if they don't exist)
    await init_db()

    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)

            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)

            # Validate password strength
            validate_password_strength(password)

            # Check if phone already exists
            if await user_repo.phone_exists(normalized_phone):
                print(f"❌ Error: Phone number {normalized_phone} already exists")
                return 1

            # Warn if users exist
            user_count = await user_repo.count_users()
            if user_count > 0:
                print(f"⚠️  Warning: {user_count} user(s) already exist in the database")
                confirm = input("   Create another system admin? (yes/no): ").strip().lower()
                if confirm != "yes":
                    print("Cancelled")
                    return 0
                print()

            # Create system admin
            print("Creating system admin...")
            user = await user_repo.create(
                phone_number=normalized_phone,
                hashed_password=hash_password(password),
                company_id=None,  # System admin has no company
                role=UserRole.SYSTEM_ADMIN.value,
            )
            # Email field exists in User model but repository doesn't set it
            # Could be added by extending User model directly after creation if needed
            await session.commit()

            print()
            print("=" * 70)
            print("✅ SYSTEM ADMIN CREATED SUCCESSFULLY!")
            print("=" * 70)
            print()
            print(f"Phone:    {user.phone_number}")
            print(f"Email:    {user.email or 'N/A'}")
            print(f"ID:       {user.id}")
            print(f"Role:     {user.role.value}")
            print()
            print("You can now login with these credentials.")
            print("=" * 70)

            return 0

        except PhoneAlreadyExistsException:
            print(f"❌ Error: Phone number already exists")
            return 1
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating system admin: {e}")
            import traceback
            traceback.print_exc()
            return 1


async def main():
    """Interactive prompt to create system admin."""
    print("=" * 70)
    print("CREATE SYSTEM ADMIN")
    print("=" * 70)
    print()

    # Get credentials
    print("Enter system admin credentials:")
    print()
    phone_number = input("Phone number: ").strip()
    if not phone_number:
        print("❌ Error: Phone number is required!")
        return 1

    email = input("Email (optional, press Enter to skip): ").strip() or None
    password = getpass("Password: ")
    if not password:
        print("❌ Error: Password is required!")
        return 1

    password_confirm = getpass("Confirm password: ")
    print()

    # Validate passwords match
    if password != password_confirm:
        print("❌ Error: Passwords don't match")
        return 1

    # Create system admin
    exit_code = await create_system_admin(phone_number, password, email)
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
