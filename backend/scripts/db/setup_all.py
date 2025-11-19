#!/usr/bin/env python3
"""Complete database setup - reset, create admin, seed data.

Usage:
    cd backend
    python scripts/db/setup_all.py

This combines:
    1. Reset database (drop & recreate tables)
    2. Create system admin (07701791983 / Admin789)
    3. Seed sample data from seed_data.json

WARNING: This will DELETE ALL DATA!
"""
import asyncio
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from core.database import AsyncSessionLocal, engine, Base, init_db
from features.users.models import User
from core.enums import UserRole
from features.users.repository import UserRepository
from features.company.models import Company
from features.product.models import Product
from features.auth.models import RefreshToken  # Required for SQLAlchemy relationship resolution


# Hardcoded admin credentials
ADMIN_PHONE = "07701791983"
ADMIN_PASSWORD = "Admin789"


async def drop_all_tables():
    """Drop all tables."""
    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ Dropped")


async def create_all_tables():
    """Create all tables."""
    print("📋 Creating tables...")
    await init_db()
    print("✅ Created")


async def create_admin():
    """Create system admin using service layer (follows architecture pattern)."""
    print("👤 Creating system admin...")

    async with AsyncSessionLocal() as session:
        try:
            # Use service layer - never bypass it
            user_repo = UserRepository(session)
            from features.users.service import UserService
            user_service = UserService(user_repo)

            user = await user_service.create_user(
                name="System Admin",
                phone_number=ADMIN_PHONE,
                password=ADMIN_PASSWORD,
                company_id=None,
                role=UserRole.SYSTEM_ADMIN.value,
            )
            await session.commit()

            print(f"✅ Admin created: {user.phone_number}")
            return user
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating admin: {e}")
            raise


async def seed_companies(companies_data: list[dict]) -> dict[str, Company]:
    """Create companies using service layer (follows architecture pattern)."""
    async with AsyncSessionLocal() as session:
        try:
            # Use service layer - never bypass it
            from features.company.repository import CompanyRepository
            from features.company.service import CompanyService

            company_repo = CompanyRepository(session)
            company_service = CompanyService(company_repo)

            companies = {}
            for data in companies_data:
                company = await company_service.create_company(name=data["name"])

                # Update is_active if needed
                if not data.get("is_active", True):
                    company = await company_service.update_company(
                        company_id=str(company.id),
                        is_active=False
                    )

                companies[company.name] = company

            await session.commit()
            print(f"✅ Created {len(companies)} companies")
            return companies
        except Exception as e:
            await session.rollback()
            raise


async def seed_users(users_data: list[dict], companies: dict[str, Company]) -> list[User]:
    """Create users using service layer (follows architecture pattern)."""
    async with AsyncSessionLocal() as session:
        try:
            # Use service layer - never bypass it
            user_repo = UserRepository(session)
            from features.users.service import UserService
            user_service = UserService(user_repo)

            users = []
            for data in users_data:
                company = companies.get(data["company_name"])
                if not company:
                    continue

                user = await user_service.create_user(
                    name=data["name"],
                    phone_number=data["phone_number"],
                    password=data["password"],
                    company_id=str(company.id),
                    role=data.get("role", "viewer"),
                    is_active=data.get("is_active", True),
                )
                users.append(user)

            await session.commit()
            print(f"✅ Created {len(users)} users")
            return users
        except Exception as e:
            await session.rollback()
            raise


async def seed_products(products_data: list[dict], companies: dict[str, Company]) -> list[Product]:
    """Create products using service layer (follows architecture pattern)."""
    async with AsyncSessionLocal() as session:
        try:
            # Use service layer - never bypass it
            from features.product.repository import ProductRepository
            from features.product.service import ProductService
            from core.company_context import CompanyContext

            product_repo = ProductRepository(session)
            product_service = ProductService(product_repo)

            # Create system admin context for product creation
            system_admin = User(
                id=uuid.uuid4(),
                name="Seed Admin",
                phone_number="+9647700000000",
                hashed_password="dummy",
                role=UserRole.SYSTEM_ADMIN,
                is_active=True,
            )
            company_ctx = CompanyContext(user=system_admin)

            products = []
            for data in products_data:
                company = companies.get(data["company_name"])
                if not company:
                    continue

                product = await product_service.create_product(
                    company_ctx=company_ctx,
                    name=data["name"],
                    sku=data["sku"],
                    selling_price=Decimal(str(data["selling_price"])),
                    description=data.get("description"),
                    cost_price=Decimal(str(data["cost_price"])) if data.get("cost_price") else None,
                    stock_quantity=data.get("stock_quantity", 0),
                    reorder_level=data.get("reorder_level", 10),
                    company_id=company.id,
                )
                products.append(product)

            await session.commit()
            print(f"✅ Created {len(products)} products")
            return products
        except Exception as e:
            await session.rollback()
            raise


async def setup_all():
    """Complete database setup."""
    print("=" * 70)
    print("⚠️  COMPLETE DATABASE SETUP")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. DELETE ALL DATA")
    print("  2. Create system admin (07701791983 / Admin789)")
    print("  3. Seed sample data from seed_data.json")
    print()

    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return 0

    print()
    print("=" * 70)
    print("SETUP STARTED")
    print("=" * 70)
    print()

    # Step 1: Reset database
    await drop_all_tables()
    print()
    await create_all_tables()
    print()

    # Step 2: Create admin
    await create_admin()
    print()

    # Step 3: Seed data
    script_dir = Path(__file__).parent
    seed_file = script_dir / "seed_data.json"

    if seed_file.exists():
        print(f"📂 Loading seed data from: {seed_file.name}")
        print()

        with open(seed_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        companies_data = config.get("companies", [])
        users_data = config.get("users", [])
        products_data = config.get("products", [])

        if companies_data:
            print("🏢 Seeding companies...")
            companies = await seed_companies(companies_data)
            print()

            if users_data:
                print("👥 Seeding users...")
                await seed_users(users_data, companies)
                print()

            if products_data:
                print("📦 Seeding products...")
                await seed_products(products_data, companies)
                print()
    else:
        print("⚠️  No seed data file found - skipping sample data")
        print()

    print("=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Credentials:")
    print(f"  Phone:    {ADMIN_PHONE}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print()
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(setup_all())
    sys.exit(exit_code)
