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
from core.security import hash_password, normalize_phone_number
from features.auth.repository import UserRepository
from features.auth.models import UserRole


# Hardcoded credentials
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
            user_repo = UserRepository(session)

            # Normalize phone
            normalized_phone = normalize_phone_number(ADMIN_PHONE)

            # Check if already exists
            if await user_repo.phone_exists(normalized_phone):
                print(f"❌ Admin with phone {normalized_phone} already exists!")
                return 1

            # Create admin
            print("Creating system admin...")
            user = await user_repo.create(
                phone_number=normalized_phone,
                hashed_password=hash_password(ADMIN_PASSWORD),
                company_id=None,  # System admin has no company
                role=UserRole.SYSTEM_ADMIN.value,
            )
            await session.commit()

            print()
            print("=" * 70)
            print("✅ SYSTEM ADMIN CREATED!")
            print("=" * 70)
            print()
            print(f"Phone:    {user.phone_number}")
            print(f"Password: {ADMIN_PASSWORD}")
            print(f"ID:       {user.id}")
            print(f"Role:     {user.role.value}")
            print()
            print("=" * 70)

            return 0

        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(create_admin())
    sys.exit(exit_code)
