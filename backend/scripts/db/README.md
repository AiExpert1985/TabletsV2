# Database Scripts

All scripts for database initialization and management.

## Quick Start

```bash
cd backend

# Complete setup (recommended)
python scripts/db/setup_all.py

# Or step by step
python scripts/db/reset_db.py       # Reset database
python scripts/db/create_admin.py   # Create admin
python scripts/db/seed_data.py      # Seed sample data
```

## Scripts

| Script | Purpose |
|--------|---------|
| `setup_all.py` | All-in-one: reset + admin + seed |
| `reset_db.py` | Drop and recreate tables |
| `create_admin.py` | Create admin (07701791983 / Admin789) |
| `seed_data.py` | Populate from seed_data.json |

## Seed Data Setup

**First time setup:**

```bash
cd scripts/db
copy seed_data.example.json seed_data.json  # Windows
# OR
cp seed_data.example.json seed_data.json    # Linux/Mac
```

Then customize `seed_data.json` with your own data (optional).

**Default test accounts** (from seed_data.example.json):

- **System Admin:** 07701791983 / Admin789
- **Company Admin:** 07701111111 / Admin123
- **Sales User:** 07702222222 / Sales123
- **Inventory User:** 07703333333 / Inventory123

**Sample data:**
- 3 companies
- 4 users
- 8 products

## Customization

Edit `seed_data.json` to add your own companies, users, and products.

**Note:** `seed_data.json` is gitignored (your custom data stays local).
