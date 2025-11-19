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
from core.enums import UserRole
from features.company.models import Company
from features.product.models import Product
from features.company.repository import CompanyRepository
from features.company.service import CompanyService
from features.users.repository import UserRepository
from features.users.service import UserService
from features.product.repository import ProductRepository
from features.product.service import ProductService
from core.company_context import CompanyContext
from features.auth.models import RefreshToken  # Required for SQLAlchemy relationship resolution


async def seed_companies(companies_data: list[dict]) -> dict[str, Company]:
    """Create companies from config data."""
    async with AsyncSessionLocal() as session:
        try:
            # Create service
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

            print(f"✅ Created {len(companies)} companies:")
            for company in companies.values():
                print(f"   - {company.name}")

            return companies
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating companies: {e}")
            raise


async def seed_users(users_data: list[dict], companies: dict[str, Company]) -> list:
    """Create users from config data."""
    async with AsyncSessionLocal() as session:
        try:
            # Create service
            user_repo = UserRepository(session)
            user_service = UserService(user_repo)

            users = []
            for data in users_data:
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Skipping user {data['phone_number']} - company not found")
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

            print(f"✅ Created {len(users)} users:")
            for user in users:
                print(f"   - {user.name} - {user.phone_number} ({user.role.value})")

            return users
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating users: {e}")
            raise


async def seed_products(products_data: list[dict], companies: dict[str, Company]) -> list:
    """Create products from config data."""
    async with AsyncSessionLocal() as session:
        try:
            # Create service
            product_repo = ProductRepository(session)
            product_service = ProductService(product_repo)

            # Create a system admin context for product creation
            # System admin can create products for any company by specifying company_id
            from features.users.models import User
            system_admin = User(
                id=uuid.uuid4(),
                name="Seed Admin",
                phone_number="+9647700000000",  # Dummy admin for seeding
                hashed_password="dummy",
                role=UserRole.SYSTEM_ADMIN,
                is_active=True,
            )
            company_ctx = CompanyContext(user=system_admin)

            products = []
            for data in products_data:
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Skipping product {data['name']} - company not found")
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
