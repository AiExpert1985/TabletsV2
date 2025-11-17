"""Database reset script - simple version.

Resets database and seeds with data from .example.json files.

Usage:
    python database_init/reset.py
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_init.operations import (
    drop_all_tables,
    create_all_tables,
    seed_system_admin,
    seed_companies,
    seed_users,
    seed_products,
)


async def reset_database():
    """Reset database and seed with example data."""
    print("=" * 70)
    print("DATABASE RESET")
    print("=" * 70)
    print()

    # Drop and create tables
    await drop_all_tables()
    print()
    await create_all_tables()
    print()

    # Load data from example files
    data_dir = Path(__file__).parent / "data"

    with open(data_dir / "system_admin.example.json") as f:
        system_admin_data = json.load(f)

    with open(data_dir / "companies.example.json") as f:
        companies_data = json.load(f)

    with open(data_dir / "users.example.json") as f:
        users_data = json.load(f)

    with open(data_dir / "products.example.json") as f:
        products_data = json.load(f)

    # Seed data
    print("👤 Creating system admin...")
    await seed_system_admin(system_admin_data)
    print()

    print("🏢 Creating companies...")
    companies = await seed_companies(companies_data)
    print()

    print("👥 Creating users...")
    await seed_users(users_data, companies)
    print()

    print("📦 Creating products...")
    await seed_products(products_data, companies)
    print()

    # Summary
    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Login:")
    print(f"  Phone:    {system_admin_data['phone_number']}")
    print(f"  Password: {system_admin_data['password']}")
    print()
    print(f"Created {len(companies)} companies, {len(users_data)} users, {len(products_data)} products")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(reset_database())
