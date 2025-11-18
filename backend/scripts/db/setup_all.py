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
from core.security import hash_password, normalize_phone_number
from features.auth.models import User, UserRole
from features.users.repository import UserRepository
from features.company.models import Company
from features.product.models import Product


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
    """Create system admin."""
    print("👤 Creating system admin...")

    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            normalized_phone = normalize_phone_number(ADMIN_PHONE)

            user = await user_repo.create(
                phone_number=normalized_phone,
                hashed_password=hash_password(ADMIN_PASSWORD),
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
    """Create companies."""
    async with AsyncSessionLocal() as session:
        try:
            companies = {}
            for data in companies_data:
                company = Company(
                    id=uuid.uuid4(),
                    name=data["name"],
                    is_active=data.get("is_active", True),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(company)
                companies[company.name] = company

            await session.commit()
            for company in companies.values():
                await session.refresh(company)

            print(f"✅ Created {len(companies)} companies")
            return companies
        except Exception as e:
            await session.rollback()
            raise


async def seed_users(users_data: list[dict], companies: dict[str, Company]) -> list[User]:
    """Create users."""
    async with AsyncSessionLocal() as session:
        try:
            users = []
            for data in users_data:
                company = companies.get(data["company_name"])
                if not company:
                    continue

                user = User(
                    id=uuid.uuid4(),
                    phone_number=normalize_phone_number(data["phone_number"]),
                    hashed_password=hash_password(data["password"]),
                    company_id=company.id,
                    role=UserRole(data.get("role", "user")),
                    company_roles=data.get("company_roles", []),
                    is_active=data.get("is_active", True),
                    is_phone_verified=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(user)
                users.append(user)

            await session.commit()
            print(f"✅ Created {len(users)} users")
            return users
        except Exception as e:
            await session.rollback()
            raise


async def seed_products(products_data: list[dict], companies: dict[str, Company]) -> list[Product]:
    """Create products."""
    async with AsyncSessionLocal() as session:
        try:
            products = []
            for data in products_data:
                company = companies.get(data["company_name"])
                if not company:
                    continue

                product = Product(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    name=data["name"],
                    sku=data["sku"],
                    description=data.get("description"),
                    cost_price=Decimal(str(data["cost_price"])),
                    selling_price=Decimal(str(data["selling_price"])),
                    stock_quantity=data.get("stock_quantity", 0),
                    reorder_level=data.get("reorder_level", 10),
                    is_active=data.get("is_active", True),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(product)
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
