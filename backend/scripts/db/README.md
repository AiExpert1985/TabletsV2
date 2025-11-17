# Database Initialization

Simple database reset and seeding for development.

## Quick Start

```bash
cd backend
python scripts/db/reset.py
# OR use the newer reset_database.py (more comprehensive)
python scripts/db/reset_database.py
```

That's it! The script reads data from `.example.json` files and populates the database.

## Structure

```
scripts/db/
├── reset.py                        # Original reset script
├── reset_database.py               # Newer comprehensive reset script
├── seed_data.example.json          # All-in-one seed data (used by reset_database.py)
├── operations.py                   # Database operations (used by reset.py)
└── data/                           # Individual seed data files (used by reset.py)
    ├── system_admin.example.json   # System admin
    ├── companies.example.json      # Companies
    ├── users.example.json          # Users
    └── products.example.json       # Products
```

## Default Test Accounts

The `.example.json` files include:

**System Admin:**
- Phone: `07700000000`
- Password: `Admin123`

**Company Admin (ACME Corp):**
- Phone: `07701111111`
- Password: `Admin123`

**Users (ACME Corp):**
- Sales: `07702222222` / `Sales123`
- Inventory: `07703333333` / `Inventory123`
- Accounting: `07704444444` / `Account123`

**Sample Data:**
- 3 companies
- 4 users
- 8 products

## Customization

Want different test data? Just edit the `.example.json` files in the `data/` folder.

**Example - Change admin password:**

Edit `data/system_admin.example.json`:
```json
{
  "phone_number": "07700000000",
  "password": "MyNewPassword123",
  "email": "admin@mycompany.com"
}
```

**Example - Add more users:**

Edit `data/users.example.json`, add more entries to the array.

**Example - Add more products:**

Edit `data/products.example.json`, add more entries to the array.

## How It Works

1. **Drops all tables** - Clean slate
2. **Creates tables** - From current models
3. **Reads .example.json files** - Loads test data
4. **Seeds database** - Populates all entities

Simple and straightforward!
