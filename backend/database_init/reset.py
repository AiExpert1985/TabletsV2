"""Database reset script.

This script resets the database and seeds it with data from JSON files.

Usage:
    # Reset with data from data/ folder (uses .json files, not .example.json)
    python database_init/reset.py

    # Reset with confirmation prompt
    python database_init/reset.py --confirm

    # Reset only (no seeding)
    python database_init/reset.py --no-seed
"""
import asyncio
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to import from backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_init.operations import (
    drop_all_tables,
    create_all_tables,
    seed_system_admin,
    seed_companies,
    seed_users,
    seed_products,
)


def load_json_file(file_path: Path) -> dict | list | None:
    """
    Load JSON file if it exists.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded data or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        sys.exit(1)


async def reset_database(
    data_dir: Path,
    skip_seed: bool = False
):
    """
    Reset database and seed with data.

    Args:
        data_dir: Directory containing seed data files
        skip_seed: If True, only reset tables without seeding
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

    if skip_seed:
        print("⚠️  Skipping seed data (--no-seed flag used)")
        print()
        print("=" * 70)
        print("✅ DATABASE RESET COMPLETE (NO SEED DATA)")
        print("=" * 70)
        return

    # Step 3: Load seed data files
    print("📂 Loading seed data files...")

    system_admin_file = data_dir / "system_admin.json"
    companies_file = data_dir / "companies.json"
    users_file = data_dir / "users.json"
    products_file = data_dir / "products.json"

    # Check if system_admin.json exists
    system_admin_data = load_json_file(system_admin_file)
    if not system_admin_data:
        print(f"❌ Required file not found: {system_admin_file}")
        print()
        print("Please copy the example files:")
        print(f"  cp {data_dir}/system_admin.example.json {system_admin_file}")
        print(f"  cp {data_dir}/companies.example.json {companies_file}")
        print(f"  cp {data_dir}/users.example.json {users_file}")
        print(f"  cp {data_dir}/products.example.json {products_file}")
        sys.exit(1)

    companies_data = load_json_file(companies_file) or []
    users_data = load_json_file(users_file) or []
    products_data = load_json_file(products_file) or []

    print(f"   ✓ system_admin.json")
    if companies_data:
        print(f"   ✓ companies.json ({len(companies_data)} companies)")
    if users_data:
        print(f"   ✓ users.json ({len(users_data)} users)")
    if products_data:
        print(f"   ✓ products.json ({len(products_data)} products)")
    print()

    # Step 4: Seed system admin
    print("👤 Creating system admin...")
    admin = await seed_system_admin(system_admin_data)
    print()

    # Step 5: Seed companies
    companies = {}
    if companies_data:
        print("🏢 Creating companies...")
        companies = await seed_companies(companies_data)
        print()

    # Step 6: Seed users
    if users_data and companies:
        print("👥 Creating users...")
        await seed_users(users_data, companies)
        print()

    # Step 7: Seed products
    if products_data and companies:
        print("📦 Creating products...")
        await seed_products(products_data, companies)
        print()

    # Summary
    print("=" * 70)
    print("✅ DATABASE RESET COMPLETE!")
    print("=" * 70)
    print()
    print("System Admin Credentials:")
    print(f"  Phone:    {system_admin_data['phone_number']}")
    print(f"  Password: {system_admin_data['password']}")
    print()

    if companies_data:
        print(f"✓ Created {len(companies)} companies")
    if users_data:
        print(f"✓ Created {len(users_data)} users")
    if products_data:
        print(f"✓ Created {len(products_data)} products")

    print()
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset database and seed with data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick reset (no confirmation)
  python database_init/reset.py

  # Reset with confirmation prompt
  python database_init/reset.py --confirm

  # Reset tables only (no seed data)
  python database_init/reset.py --no-seed

Data Files:
  The script reads seed data from database_init/data/:
    - system_admin.json (required)
    - companies.json (optional)
    - users.json (optional)
    - products.json (optional)

  First time setup:
    cd database_init/data
    cp system_admin.example.json system_admin.json
    cp companies.example.json companies.json
    cp users.example.json users.json
    cp products.example.json products.json

  Then customize the .json files as needed.
        """
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Ask for confirmation before resetting'
    )

    parser.add_argument(
        '--no-seed',
        action='store_true',
        help='Only reset tables, do not seed data'
    )

    args = parser.parse_args()

    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"

    # Confirm if requested
    if args.confirm:
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

    # Run reset
    asyncio.run(reset_database(data_dir, skip_seed=args.no_seed))


if __name__ == "__main__":
    main()
