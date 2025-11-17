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

<<<<<<< HEAD
=======
## Seed Data
>>>>>>> claude/review-project-docs-01PXqRQ4Wc8zMG7drFtauQZr

**Default accounts:**

- **System Admin:** 07701791983 / Admin789 (created by create_admin.py)
- **Company Admin:** 07701111111 / Admin123 (from seed_data.json)
- **Sales User:** 07702222222 / Sales123 (from seed_data.json)
- **Inventory User:** 07703333333 / Inventory123 (from seed_data.json)

**Sample data:**
- 3 companies
- 4 users
- 8 products

## Customization

Edit `seed_data.json` to add your own companies, users, and products.
