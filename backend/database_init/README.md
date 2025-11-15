# Database Initialization

This folder contains all database initialization code and seed data.

## Structure

```
database_init/
├── reset.py              # Main script to reset and seed database
├── operations.py         # Database operations (drop, create, seed)
├── data/                 # Seed data files (JSON)
│   ├── system_admin.json          # System admin credentials
│   ├── companies.json             # Test companies
│   ├── users.json                 # Test user accounts
│   ├── products.json              # Test products
│   ├── system_admin.example.json  # Template for system admin
│   ├── companies.example.json     # Template for companies
│   ├── users.example.json         # Template for users
│   └── products.example.json      # Template for products
└── README.md             # This file
```

## Quick Start

### First Time Setup (Windows)

```batch
cd backend\database_init
setup.bat
python reset.py
```

### First Time Setup (Linux/Mac)

```bash
cd backend/database_init
./setup.sh
python reset.py
```

### Manual Setup (All Platforms)

If you prefer to do it manually:

1. **Copy example data files:**
   ```bash
   cd database_init/data
   cp system_admin.example.json system_admin.json
   cp companies.example.json companies.json
   cp users.example.json users.json
   cp products.example.json products.json
   ```

2. **(Optional) Customize the data:**
   Edit the `.json` files to change passwords, add more data, etc.

3. **Reset and seed database:**
   ```bash
   cd ..
   python reset.py
   ```

### During Development

Every time you need a fresh database:

```bash
python database_init/reset.py
```

**That's it!** No confirmations, no manual input.

## Usage Options

### Quick Reset (Default)

Resets database and seeds all data without confirmation:

```bash
python database_init/reset.py
```

### Reset with Confirmation

Asks for confirmation before proceeding:

```bash
python database_init/reset.py --confirm
```

### Reset Only (No Seed)

Drops and recreates tables without seeding any data:

```bash
python database_init/reset.py --no-seed
```

## Data Files

### system_admin.json (Required)

System administrator account:

```json
{
  "phone_number": "07700000000",
  "password": "Admin123",
  "email": "sysadmin@example.com"
}
```

**This file is required.** The script will fail if it doesn't exist.

### companies.json (Optional)

Test companies for multi-tenancy:

```json
[
  {
    "name": "ACME Corporation",
    "is_active": true
  }
]
```

If this file is missing or empty, no companies will be created.

### users.json (Optional)

Test user accounts linked to companies:

```json
[
  {
    "phone_number": "07701111111",
    "password": "Admin123",
    "email": "admin@acme.com",
    "company_name": "ACME Corporation",
    "role": "company_admin",
    "company_roles": ["sales", "inventory"]
  }
]
```

**Important:** `company_name` must match a company name from `companies.json`.

Available roles:
- `system_admin` - Full system access (no company)
- `company_admin` - Full company access
- `user` - Limited access based on company_roles

### products.json (Optional)

Test products linked to companies:

```json
[
  {
    "company_name": "ACME Corporation",
    "name": "Laptop - Dell XPS 15",
    "sku": "DELL-XPS15-001",
    "description": "High-performance laptop",
    "cost_price": "800.00",
    "selling_price": "1200.00",
    "stock_quantity": 15,
    "reorder_level": 5,
    "is_active": true
  }
]
```

**Important:** `company_name` must match a company name from `companies.json`.

## Default Test Accounts

The example files include these test accounts:

### System Admin (Full Access)
- Phone: `07700000000`
- Password: `Admin123`
- Access: All companies, all features

### Company Admin (ACME Corp)
- Phone: `07701111111`
- Password: `Admin123`
- Access: All ACME features

### Sales User (ACME Corp)
- Phone: `07702222222`
- Password: `Sales123`
- Access: Sales features only

### Inventory User (ACME Corp)
- Phone: `07703333333`
- Password: `Inventory123`
- Access: Inventory features only

### Accounting User (ACME Corp)
- Phone: `07704444444`
- Password: `Account123`
- Access: Accounting features only

## Customization

### Add Your Own Data

Edit the JSON files to add more:
- Companies
- Users with different roles
- Products with varying stock levels
- Test scenarios (inactive users, low stock items, etc.)

### Create Multiple Scenarios

You can create multiple sets of data files:
- `data/minimal/` - Just system admin
- `data/testing/` - Full test data
- `data/demo/` - Demo data for presentations

Then modify `reset.py` to accept a `--data-dir` argument.

## Security

**Important:**
- All `.json` files (without `.example`) are gitignored
- Only `.example.json` files are committed to the repository
- Never commit real passwords to git
- The `.json` files are for development only

## Troubleshooting

### Error: system_admin.json not found

Copy the example file:
```bash
cp data/system_admin.example.json data/system_admin.json
```

### Error: Company not found for user/product

Make sure the `company_name` in users/products matches exactly with a company name in `companies.json`.

### Error: Invalid JSON

Validate your JSON:
```bash
python -m json.tool data/system_admin.json
```

### Database locked (SQLite)

Make sure the backend server is stopped before resetting:
```bash
# Stop the backend (Ctrl+C)
# Then run reset
python database_init/reset.py
```

## Integration with Development Workflow

### Typical Development Cycle

1. Make changes to models
2. Reset database: `python database_init/reset.py`
3. Start backend: `python main.py`
4. Test with Flutter app
5. Repeat

### Testing Different User Roles

Use the test accounts to verify permissions:
- System admin: Test cross-company features
- Company admin: Test company management
- Regular users: Test role-based restrictions

## Code Organization

### operations.py

Contains pure database operations:
- `drop_all_tables()` - Drop all tables
- `create_all_tables()` - Create tables from models
- `seed_system_admin(data)` - Create system admin
- `seed_companies(data)` - Create companies
- `seed_users(data, companies)` - Create users
- `seed_products(data, companies)` - Create products

**All operations are async** and handle their own transactions.

### reset.py

Orchestrates the reset process:
1. Parse command-line arguments
2. Load JSON data files
3. Call operations in correct order
4. Display summary

**This is the entry point** - run this script to reset the database.

## Future Enhancements

Potential improvements:
- Support for more entity types (customers, orders, etc.)
- Validation of seed data against schemas
- Backup before reset
- Selective seeding (e.g., only products)
- Data generators for large datasets
