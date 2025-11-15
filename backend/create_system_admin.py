"""Script to create a system admin user in the database.

Usage:
    python create_system_admin.py

Environment variables required:
    - DATABASE_URL: Database connection string
    - JWT_SECRET_KEY: Secret key for JWT tokens
"""
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from core.database import AsyncSessionLocal, init_db
from core.security import hash_password
from features.auth.models import User, UserRole


async def create_system_admin(
    phone_number: str,
    password: str,
    email: str | None = None
) -> None:
    """Create a system admin user.

    Args:
        phone_number: Phone number for the admin
        password: Password for the admin
        email: Optional email address
    """
    # Initialize database (create tables if they don't exist)
    await init_db()

    async with AsyncSessionLocal() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.phone_number == phone_number)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"❌ User with phone number {phone_number} already exists!")
                print(f"   User ID: {existing_user.id}")
                print(f"   Role: {existing_user.role}")
                print(f"   Active: {existing_user.is_active}")

                # Ask if user wants to update to system admin
                response = input("\nDo you want to update this user to system_admin? (yes/no): ")
                if response.lower() == 'yes':
                    existing_user.role = UserRole.SYSTEM_ADMIN
                    existing_user.company_id = None  # System admin has no company
                    existing_user.company_roles = []  # Clear company roles
                    existing_user.is_active = True
                    existing_user.hashed_password = hash_password(password)
                    if email:
                        existing_user.email = email

                    await session.commit()
                    print(f"✅ User updated to system admin successfully!")
                    print(f"   Phone: {existing_user.phone_number}")
                    print(f"   Email: {existing_user.email}")
                    print(f"   Role: {existing_user.role}")
                else:
                    print("Operation cancelled.")
                return

            # Hash password
            hashed_password = hash_password(password)

            # Create new system admin user
            admin_user = User(
                id=uuid.uuid4(),
                phone_number=phone_number,
                email=email,
                hashed_password=hashed_password,
                company_id=None,  # System admin has no company
                role=UserRole.SYSTEM_ADMIN,
                company_roles=[],  # System admin doesn't need company roles
                is_active=True,
                is_phone_verified=True,  # Auto-verify for admin
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            session.add(admin_user)
            await session.commit()

            print("=" * 60)
            print("✅ System admin created successfully!")
            print("=" * 60)
            print(f"User ID:      {admin_user.id}")
            print(f"Phone:        {admin_user.phone_number}")
            print(f"Email:        {admin_user.email or 'N/A'}")
            print(f"Role:         {admin_user.role}")
            print(f"Company ID:   {admin_user.company_id or 'N/A (System Admin)'}")
            print(f"Active:       {admin_user.is_active}")
            print(f"Verified:     {admin_user.is_phone_verified}")
            print("=" * 60)
            print("\nYou can now login with:")
            print(f"  Phone:    {phone_number}")
            print(f"  Password: {password}")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating system admin: {e}")
            raise


async def main():
    """Interactive prompt to create system admin."""
    print("=" * 60)
    print("CREATE SYSTEM ADMIN USER")
    print("=" * 60)
    print()

    # Get phone number
    phone_number = input("Enter phone number: ").strip()
    if not phone_number:
        print("❌ Phone number is required!")
        sys.exit(1)

    # Get password
    password = input("Enter password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit): ").strip()
    if not password:
        print("❌ Password is required!")
        sys.exit(1)

    # Validate password strength
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        sys.exit(1)

    # Get optional email
    email = input("Enter email (optional, press Enter to skip): ").strip()
    email = email if email else None

    print()
    print("Creating system admin with:")
    print(f"  Phone:    {phone_number}")
    print(f"  Email:    {email or 'N/A'}")
    print()

    confirm = input("Proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    print()
    await create_system_admin(phone_number, password, email)


if __name__ == "__main__":
    asyncio.run(main())
