#!/usr/bin/env python3
"""Reset database - drop and recreate all tables.

Usage:
    cd backend
    python scripts/db/reset_db.py

WARNING: This will DELETE ALL DATA!
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from core.database import engine, Base, init_db


async def drop_all_tables():
    """Drop all tables."""
    print("🗑️  Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ All tables dropped")


async def create_all_tables():
    """Create all tables."""
    print("📋 Creating tables...")
    await init_db()
    print("✅ Tables created")


async def reset_database():
    """Reset database."""
    print("=" * 70)
    print("⚠️  WARNING: DATABASE RESET")
    print("=" * 70)
    print()
    print("This will DELETE ALL DATA!")
    print()

    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return 0

    print()
    print("=" * 70)
    print("RESETTING DATABASE")
    print("=" * 70)
    print()

    await drop_all_tables()
    print()
    await create_all_tables()

    print()
    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Create admin: python scripts/admin/create_admin.py")
    print("  2. Seed data:    python scripts/db/seed_data.py")
    print()
    print("Or run both:  python scripts/db/setup_all.py")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(reset_database())
    sys.exit(exit_code)
