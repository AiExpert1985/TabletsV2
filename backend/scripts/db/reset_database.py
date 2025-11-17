"""Script to reset database and seed initial data.

This script will:
1. Drop all existing tables
2. Recreate tables with current schema
3. Create a system admin user
4. Optionally seed sample data (companies, users, products)

Usage:
    # Interactive mode (prompts for inputs)
    python reset_database.py

    # Config file mode (uses seed_data.json)
    python reset_database.py --config seed_data.json

    # Quick reset with config (no confirmations)
    python reset_database.py --config seed_data.json --yes
"""
import asyncio
import sys
import json
import argparse
import uuid
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
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


async def seed_companies_from_config(companies_data: list[dict]) -> dict[str, Company]:
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
                print(f"   - {company.name} (ID: {company.id})")

            return companies
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating companies: {e}")
            raise


async def seed_users_from_config(
    users_data: list[dict],
    companies: dict[str, Company]
) -> list[User]:
    """Create users from config data."""
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


async def seed_products_from_config(
    products_data: list[dict],
    companies: dict[str, Company]
) -> list[Product]:
    """Create products from config data."""
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


async def reset_database_from_config(config_path: Path):
    """Reset database using configuration file."""
    # Load config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        print(f"\nCreate it by copying the example:")
        print(f"  cp seed_data.example.json seed_data.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        sys.exit(1)

    print("=" * 70)
    print("DATABASE RESET FROM CONFIG")
    print("=" * 70)
    print(f"Config file: {config_path}")
    print()

    # Step 1: Drop all tables
    await drop_all_tables()
    print()

    # Step 2: Create tables
    await create_all_tables()
    print()

    # Step 3: Create system admin
    print("👤 Creating system admin...")
    admin_config = config.get("system_admin", {})
    if not admin_config:
        print("❌ No system_admin found in config file")
        sys.exit(1)

    await create_system_admin(
        phone_number=admin_config["phone_number"],
        password=admin_config["password"],
        email=admin_config.get("email")
    )
    print()

    # Step 4: Seed companies
    companies_data = config.get("companies", [])
    companies = {}
    if companies_data:
        print("🏢 Creating companies...")
        companies = await seed_companies_from_config(companies_data)
        print()

    # Step 5: Seed users
    users_data = config.get("users", [])
    if users_data and companies:
        print("👥 Creating users...")
        await seed_users_from_config(users_data, companies)
        print()

    # Step 6: Seed products
    products_data = config.get("products", [])
    if products_data and companies:
        print("📦 Creating products...")
        await seed_products_from_config(products_data, companies)
        print()

    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Credentials:")
    print(f"  Phone:    {admin_config['phone_number']}")
    print(f"  Password: {admin_config['password']}")
    print()

    if companies_data:
        print(f"Created {len(companies)} companies")
    if users_data:
        print(f"Created {len(users_data)} users")
    if products_data:
        print(f"Created {len(products_data)} products")
    print()
    print("=" * 70)


async def reset_database_interactive():
    """Reset database with interactive prompts."""
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
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"System Admin Phone: {phone}")
    print(f"System Admin Email: {email or 'N/A'}")
    print()

    final_confirm = input("Proceed with database reset? (yes/no): ")
    if final_confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    print()
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
    await create_system_admin(phone, password, email)
    print()

    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Credentials:")
    print(f"  Phone:    {phone}")
    print(f"  Password: {password}")
    print()
    print("=" * 70)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Reset database and seed initial data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for inputs)
  python reset_database.py

  # Use config file
  python reset_database.py --config seed_data.json

  # Quick reset with config (skip confirmations)
  python reset_database.py --config seed_data.json --yes

Config file format:
  See seed_data.example.json for the expected structure.
  Copy it to seed_data.json and customize as needed:
    cp seed_data.example.json seed_data.json
        """
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='Path to JSON config file with seed data'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts (use with --config)'
    )

    args = parser.parse_args()

    # Config file mode
    if args.config:
        if args.yes:
            # Skip confirmation, just run
            asyncio.run(reset_database_from_config(args.config))
        else:
            # Ask for confirmation
            print("=" * 70)
            print("⚠️  WARNING: DATABASE RESET")
            print("=" * 70)
            print()
            print("This will DELETE ALL DATA and recreate the database!")
            print(f"Config file: {args.config}")
            print()
            confirm = input("Are you sure you want to continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Operation cancelled.")
                sys.exit(0)
            print()
            asyncio.run(reset_database_from_config(args.config))
    else:
        # Interactive mode
        asyncio.run(reset_database_interactive())


if __name__ == "__main__":
    main()
