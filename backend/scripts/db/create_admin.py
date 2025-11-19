#!/usr/bin/env python3
"""Create system admin with hardcoded credentials.

Usage:
    cd backend
    python scripts/admin/create_admin.py

Creates admin with:
    Phone: 07701791983
    Password: Admin789
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from core.database import AsyncSessionLocal, init_db
from features.users.repository import UserRepository
from features.users.service import UserService
from core.enums import UserRole
from core.exceptions import PhoneAlreadyExistsException


# Hardcoded credentials
ADMIN_NAME = "System Administrator"
ADMIN_PHONE = "07701791983"
ADMIN_PASSWORD = "Admin789"


async def create_admin():
    """Create system admin with hardcoded credentials."""
    print("=" * 70)
    print("CREATE SYSTEM ADMIN")
    print("=" * 70)
    print()

    # Initialize database
    await init_db()

    async with AsyncSessionLocal() as session:
        try:
            # Create service
            user_repo = UserRepository(session)
            user_service = UserService(user_repo)

            # Create admin using service
            print("Creating system admin...")
            user = await user_service.create_user(
                name=ADMIN_NAME,
                phone_number=ADMIN_PHONE,
                password=ADMIN_PASSWORD,
                company_id=None,  # System admin has no company
                role=UserRole.SYSTEM_ADMIN.value,
            )
            await session.commit()

            print()
            print("=" * 70)
            print("✅ SYSTEM ADMIN CREATED!")
            print("=" * 70)
            print()
            print(f"Name:     {user.name}")
            print(f"Phone:    {user.phone_number}")
            print(f"Password: {ADMIN_PASSWORD}")
            print(f"ID:       {user.id}")
            print(f"Role:     {user.role.value}")
            print()
            print("=" * 70)

            return 0

        except PhoneAlreadyExistsException:
            print(f"❌ Admin with phone {ADMIN_PHONE} already exists!")
            return 1
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(create_admin())
    sys.exit(exit_code)
