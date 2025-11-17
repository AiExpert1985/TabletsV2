#!/usr/bin/env python3
"""Seed database with sample data from JSON file.

Usage:
    cd backend
    python scripts/db/seed_data.py

Reads from: scripts/db/seed_data.json (or seed_data.example.json)
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

from core.database import AsyncSessionLocal
from core.security import hash_password, normalize_phone_number
from features.auth.models import User, UserRole
from features.company.models import Company
from features.product.models import Product


async def seed_companies(companies_data: list[dict]) -> dict[str, Company]:
    """Create companies from config data."""
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

            # Refresh to get IDs
            for company in companies.values():
                await session.refresh(company)

            print(f"✅ Created {len(companies)} companies:")
            for company in companies.values():
                print(f"   - {company.name}")

            return companies
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating companies: {e}")
            raise


async def seed_users(users_data: list[dict], companies: dict[str, Company]) -> list[User]:
    """Create users from config data."""
    async with AsyncSessionLocal() as session:
        try:
            users = []
            for data in users_data:
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Skipping user {data['phone_number']} - company not found")
                    continue

                normalized_phone = normalize_phone_number(data["phone_number"])

                user = User(
                    id=uuid.uuid4(),
                    phone_number=normalized_phone,
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

            print(f"✅ Created {len(users)} users:")
            for user in users:
                print(f"   - {user.phone_number} ({user.role.value})")

            return users
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating users: {e}")
            raise


async def seed_products(products_data: list[dict], companies: dict[str, Company]) -> list[Product]:
    """Create products from config data."""
    async with AsyncSessionLocal() as session:
        try:
            products = []
            for data in products_data:
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Skipping product {data['name']} - company not found")
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

            print(f"✅ Created {len(products)} products:")
            for product in products:
                status = "🔴" if product.stock_quantity <= product.reorder_level else "✅"
                print(f"   - {product.name} (Stock: {product.stock_quantity}) {status}")

            return products
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating products: {e}")
            raise


async def seed_all():
    """Seed database with all data from JSON file."""
    # Find seed data file
    script_dir = Path(__file__).parent
    seed_file = script_dir / "seed_data.json"

    if not seed_file.exists():
        seed_file = script_dir / "seed_data.example.json"

    if not seed_file.exists():
        print("❌ Error: No seed_data.json or seed_data.example.json found!")
        print(f"   Expected location: {script_dir}/seed_data.json")
        return 1

    # Load data
    print(f"📂 Loading data from: {seed_file.name}")
    print()

    try:
        with open(seed_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return 1

    print("=" * 70)
    print("SEEDING DATABASE")
    print("=" * 70)
    print()

    # Seed companies
    companies_data = config.get("companies", [])
    companies = {}
    if companies_data:
        print("🏢 Creating companies...")
        companies = await seed_companies(companies_data)
        print()

    # Seed users
    users_data = config.get("users", [])
    if users_data and companies:
        print("👥 Creating users...")
        await seed_users(users_data, companies)
        print()

    # Seed products
    products_data = config.get("products", [])
    if products_data and companies:
        print("📦 Creating products...")
        await seed_products(products_data, companies)
        print()

    print("=" * 70)
    print("✅ SEEDING COMPLETE!")
    print("=" * 70)
    print()
    print(f"Created: {len(companies)} companies, {len(users_data)} users, {len(products_data)} products")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(seed_all())
    sys.exit(exit_code)
