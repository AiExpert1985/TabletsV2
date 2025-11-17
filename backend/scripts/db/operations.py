"""Database operations for initialization and seeding.

This module contains all database operations:
- Drop and create tables
- Seed data from JSON files
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
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


async def seed_system_admin(admin_data: dict) -> User:
    """
    Create system admin user.

    Args:
        admin_data: Dict with phone_number, password, and optional email

    Returns:
        Created User instance
    """
    async with AsyncSessionLocal() as session:
        try:
            admin_user = User(
                id=uuid.uuid4(),
                phone_number=admin_data["phone_number"],
                email=admin_data.get("email"),
                hashed_password=hash_password(admin_data["password"]),
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


async def seed_companies(companies_data: list[dict]) -> dict[str, Company]:
    """
    Create companies from data.

    Args:
        companies_data: List of company dicts with name and is_active

    Returns:
        Dict mapping company name to Company instance
    """
    if not companies_data:
        return {}

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
                print(f"   - {company.name} (ID: {company.id})")

            return companies
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating companies: {e}")
            raise


async def seed_users(
    users_data: list[dict],
    companies: dict[str, Company]
) -> list[User]:
    """
    Create users from data.

    Args:
        users_data: List of user dicts
        companies: Dict mapping company name to Company instance

    Returns:
        List of created User instances
    """
    if not users_data:
        return []

    async with AsyncSessionLocal() as session:
        try:
            users = []
            for data in users_data:
                # Get company by name
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Warning: Company '{data['company_name']}' not found for user {data['phone_number']}")
                    continue

                user = User(
                    id=uuid.uuid4(),
                    phone_number=data["phone_number"],
                    email=data.get("email"),
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

            for user in users:
                await session.refresh(user)

            print(f"✅ Created {len(users)} users:")
            for user in users:
                print(f"   - {user.phone_number} ({user.role.value}) - {user.email}")

            return users
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating users: {e}")
            raise


async def seed_products(
    products_data: list[dict],
    companies: dict[str, Company]
) -> list[Product]:
    """
    Create products from data.

    Args:
        products_data: List of product dicts
        companies: Dict mapping company name to Company instance

    Returns:
        List of created Product instances
    """
    if not products_data:
        return []

    async with AsyncSessionLocal() as session:
        try:
            products = []
            for data in products_data:
                # Get company by name
                company = companies.get(data["company_name"])
                if not company:
                    print(f"⚠️  Warning: Company '{data['company_name']}' not found for product {data['name']}")
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

            for product in products:
                await session.refresh(product)

            print(f"✅ Created {len(products)} products:")
            for product in products:
                stock_status = "🔴 LOW STOCK" if product.stock_quantity <= product.reorder_level else "✅"
                print(f"   - {product.name} | Stock: {product.stock_quantity} {stock_status}")

            return products
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating products: {e}")
            raise
