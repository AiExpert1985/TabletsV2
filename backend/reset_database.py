"""Script to reset database and seed initial data.

This script will:
1. Drop all existing tables
2. Recreate tables with current schema
3. Create a system admin user
4. Optionally seed sample data (companies, users, products)

Usage:
    python reset_database.py
"""
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text
from core.database import AsyncSessionLocal, init_db, engine, Base
from core.security import hash_password
from features.auth.models import User, UserRole
from features.company.models import Company
from features.product.models import Product


async def drop_all_tables():
    """Drop all tables in the database."""
    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ All tables dropped")


async def create_all_tables():
    """Create all tables with current schema."""
    print("📋 Creating tables...")
    await init_db()
    print("✅ Tables created")


async def create_system_admin(
    phone_number: str,
    password: str,
    email: str | None = None
) -> User:
    """Create system admin user."""
    async with AsyncSessionLocal() as session:
        try:
            admin_user = User(
                id=uuid.uuid4(),
                phone_number=phone_number,
                email=email,
                hashed_password=hash_password(password),
                company_id=None,  # System admin has no company
                role=UserRole.SYSTEM_ADMIN,
                company_roles=[],
                is_active=True,
                is_phone_verified=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print(f"✅ System admin created:")
            print(f"   Phone: {admin_user.phone_number}")
            print(f"   Email: {admin_user.email or 'N/A'}")
            print(f"   ID: {admin_user.id}")

            return admin_user
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating system admin: {e}")
            raise


async def seed_sample_companies() -> list[Company]:
    """Create sample companies for testing."""
    companies_data = [
        {"name": "ACME Corporation", "is_active": True},
        {"name": "TechStart Solutions", "is_active": True},
        {"name": "Global Traders Inc", "is_active": True},
    ]

    async with AsyncSessionLocal() as session:
        try:
            companies = []
            for data in companies_data:
                company = Company(
                    id=uuid.uuid4(),
                    name=data["name"],
                    is_active=data["is_active"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(company)
                companies.append(company)

            await session.commit()

            # Refresh to get IDs
            for company in companies:
                await session.refresh(company)

            print(f"✅ Created {len(companies)} sample companies:")
            for company in companies:
                print(f"   - {company.name} (ID: {company.id})")

            return companies
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating companies: {e}")
            raise


async def seed_sample_users(companies: list[Company]) -> list[User]:
    """Create sample users for testing."""
    if not companies:
        print("⚠️  No companies provided, skipping user creation")
        return []

    # Create users for the first company
    company = companies[0]

    users_data = [
        {
            "phone": "07701111111",
            "password": "Admin123",
            "email": "admin@acme.com",
            "role": UserRole.COMPANY_ADMIN,
            "company_roles": ["sales", "inventory"],
        },
        {
            "phone": "07702222222",
            "password": "User123",
            "email": "sales@acme.com",
            "role": UserRole.USER,
            "company_roles": ["sales"],
        },
        {
            "phone": "07703333333",
            "password": "User123",
            "email": "inventory@acme.com",
            "role": UserRole.USER,
            "company_roles": ["inventory"],
        },
    ]

    async with AsyncSessionLocal() as session:
        try:
            users = []
            for data in users_data:
                user = User(
                    id=uuid.uuid4(),
                    phone_number=data["phone"],
                    email=data["email"],
                    hashed_password=hash_password(data["password"]),
                    company_id=company.id,
                    role=data["role"],
                    company_roles=data["company_roles"],
                    is_active=True,
                    is_phone_verified=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(user)
                users.append(user)

            await session.commit()

            for user in users:
                await session.refresh(user)

            print(f"✅ Created {len(users)} sample users for {company.name}:")
            for user in users:
                print(f"   - {user.phone_number} ({user.role.value}) - {user.email}")

            return users
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating users: {e}")
            raise


async def seed_sample_products(companies: list[Company]) -> list[Product]:
    """Create sample products for testing."""
    if not companies:
        print("⚠️  No companies provided, skipping product creation")
        return []

    # Create products for the first company
    company = companies[0]

    products_data = [
        {
            "name": "Laptop - Dell XPS 15",
            "sku": "DELL-XPS15-001",
            "description": "High-performance laptop for business",
            "cost_price": Decimal("800.00"),
            "selling_price": Decimal("1200.00"),
            "stock_quantity": 15,
            "reorder_level": 5,
        },
        {
            "name": "Wireless Mouse",
            "sku": "MS-WL-001",
            "description": "Ergonomic wireless mouse",
            "cost_price": Decimal("10.00"),
            "selling_price": Decimal("25.00"),
            "stock_quantity": 50,
            "reorder_level": 20,
        },
        {
            "name": "USB-C Hub",
            "sku": "HUB-USBC-001",
            "description": "7-in-1 USB-C hub with HDMI",
            "cost_price": Decimal("20.00"),
            "selling_price": Decimal("45.00"),
            "stock_quantity": 3,  # Low stock!
            "reorder_level": 10,
        },
        {
            "name": "Office Chair",
            "sku": "CHAIR-ERG-001",
            "description": "Ergonomic office chair with lumbar support",
            "cost_price": Decimal("150.00"),
            "selling_price": Decimal("300.00"),
            "stock_quantity": 8,
            "reorder_level": 5,
        },
        {
            "name": "Monitor - 27\" 4K",
            "sku": "MON-27-4K-001",
            "description": "27-inch 4K UHD monitor",
            "cost_price": Decimal("300.00"),
            "selling_price": Decimal("500.00"),
            "stock_quantity": 12,
            "reorder_level": 5,
        },
    ]

    async with AsyncSessionLocal() as session:
        try:
            products = []
            for data in products_data:
                product = Product(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    name=data["name"],
                    sku=data["sku"],
                    description=data["description"],
                    cost_price=data["cost_price"],
                    selling_price=data["selling_price"],
                    stock_quantity=data["stock_quantity"],
                    reorder_level=data["reorder_level"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(product)
                products.append(product)

            await session.commit()

            for product in products:
                await session.refresh(product)

            print(f"✅ Created {len(products)} sample products for {company.name}:")
            for product in products:
                stock_status = "🔴 LOW STOCK" if product.stock_quantity <= product.reorder_level else "✅"
                print(f"   - {product.name} | Stock: {product.stock_quantity} {stock_status}")

            return products
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating products: {e}")
            raise


async def reset_database(
    admin_phone: str,
    admin_password: str,
    admin_email: str | None = None,
    seed_sample_data: bool = False
):
    """
    Reset database completely and seed initial data.

    Args:
        admin_phone: Phone number for system admin
        admin_password: Password for system admin
        admin_email: Optional email for system admin
        seed_sample_data: Whether to create sample companies, users, and products
    """
    print("=" * 70)
    print("DATABASE RESET")
    print("=" * 70)
    print()

    # Step 1: Drop all tables
    await drop_all_tables()
    print()

    # Step 2: Create tables
    await create_all_tables()
    print()

    # Step 3: Create system admin
    print("👤 Creating system admin...")
    await create_system_admin(admin_phone, admin_password, admin_email)
    print()

    # Step 4: Optionally seed sample data
    if seed_sample_data:
        print("🌱 Seeding sample data...")
        print()

        companies = await seed_sample_companies()
        print()

        users = await seed_sample_users(companies)
        print()

        products = await seed_sample_products(companies)
        print()

    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Credentials:")
    print(f"  Phone:    {admin_phone}")
    print(f"  Password: {admin_password}")
    print()

    if seed_sample_data:
        print("Sample Data Created:")
        print("  - 3 companies")
        print("  - 3 users (for ACME Corporation)")
        print("  - 5 products (for ACME Corporation)")
        print()
        print("Sample Company Admin Login:")
        print("  Phone:    07701111111")
        print("  Password: Admin123")
        print()

    print("=" * 70)


async def main():
    """Interactive prompt to reset database."""
    print("=" * 70)
    print("⚠️  WARNING: DATABASE RESET")
    print("=" * 70)
    print()
    print("This will DELETE ALL DATA and recreate the database!")
    print()

    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    print()
    print("=" * 70)
    print("SYSTEM ADMIN SETUP")
    print("=" * 70)
    print()

    # Get system admin details
    phone = input("Enter system admin phone number: ").strip()
    if not phone:
        print("❌ Phone number is required!")
        sys.exit(1)

    password = input("Enter system admin password (min 8 chars): ").strip()
    if not password or len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        sys.exit(1)

    email = input("Enter system admin email (optional): ").strip()
    email = email if email else None

    print()

    # Ask about sample data
    seed_data = input("Create sample data for testing? (yes/no): ")
    seed_sample_data = seed_data.lower() == 'yes'

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"System Admin Phone: {phone}")
    print(f"System Admin Email: {email or 'N/A'}")
    print(f"Seed Sample Data:   {'Yes' if seed_sample_data else 'No'}")
    print()

    final_confirm = input("Proceed with database reset? (yes/no): ")
    if final_confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    print()
    await reset_database(phone, password, email, seed_sample_data)


if __name__ == "__main__":
    asyncio.run(main())
