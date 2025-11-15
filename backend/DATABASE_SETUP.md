# Database Setup and Reset

This guide explains how to set up and reset the database during development.

## Quick Start

### First Time Setup

1. **Copy the seed data template:**
   ```bash
   cd backend
   cp seed_data.example.json seed_data.json
   ```

2. **Edit seed_data.json** with your credentials (optional - defaults work fine for development)

3. **Reset and seed the database:**
   ```bash
   python reset_database.py --config seed_data.json --yes
   ```

4. **Start the backend:**
   ```bash
   python main.py
   ```

5. **Login with system admin:**
   - Phone: `07700000000`
   - Password: `Admin123`

## Usage Options

### Option 1: Quick Reset with Config (Recommended for Development)

Use this when you want to quickly reset the database with the same test data:

```bash
python reset_database.py --config seed_data.json --yes
```

**Advantages:**
- No manual input required
- Consistent test data every time
- Fast - perfect for rapid development cycles
- Safe - seed_data.json is gitignored (won't accidentally commit passwords)

### Option 2: Config with Confirmation

Use this when you want to review before resetting:

```bash
python reset_database.py --config seed_data.json
```

Will ask for confirmation before proceeding.

### Option 3: Interactive Mode

Use this when you need a custom setup (production, one-time setups):

```bash
python reset_database.py
```

Will prompt for:
- System admin phone number
- System admin password
- System admin email (optional)

**Note:** Interactive mode only creates the system admin, no sample data.

## Seed Data Configuration

The `seed_data.json` file contains:

### System Admin
```json
{
  "system_admin": {
    "phone_number": "07700000000",
    "password": "Admin123",
    "email": "sysadmin@example.com"
  }
}
```

### Companies
```json
{
  "companies": [
    {
      "name": "ACME Corporation",
      "is_active": true
    }
  ]
}
```

### Users
```json
{
  "users": [
    {
      "phone_number": "07701111111",
      "password": "Admin123",
      "email": "admin@acme.com",
      "company_name": "ACME Corporation",
      "role": "company_admin",
      "company_roles": ["sales", "inventory", "accounting"]
    }
  ]
}
```

### Products
```json
{
  "products": [
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
}
```

## Default Test Accounts

The `seed_data.example.json` includes these default accounts:

### System Admin
- Phone: `07700000000`
- Password: `Admin123`
- Role: System Admin (full access)

### Company Admin (ACME Corporation)
- Phone: `07701111111`
- Password: `Admin123`
- Role: Company Admin
- Permissions: sales, inventory, accounting

### Sales User (ACME Corporation)
- Phone: `07702222222`
- Password: `Sales123`
- Role: User
- Permissions: sales

### Inventory User (ACME Corporation)
- Phone: `07703333333`
- Password: `Inventory123`
- Role: User
- Permissions: inventory

### Accounting User (ACME Corporation)
- Phone: `07704444444`
- Password: `Account123`
- Role: User
- Permissions: accounting

## Sample Data

The seed file includes:
- **3 companies** (ACME Corporation, TechStart Solutions, Global Traders Inc)
- **4 users** for ACME Corporation (1 admin, 3 regular users)
- **8 products** for ACME Corporation (including some with low stock)

## Common Workflows

### During Active Development

When making frequent model changes:

```bash
# Make changes to models
# Reset database with test data
python reset_database.py --config seed_data.json --yes

# Start backend
python main.py
```

### Testing Different User Roles

Use the different test accounts to verify permissions:

1. Test system admin features with `07700000000`
2. Test company admin features with `07701111111`
3. Test sales user with `07702222222`
4. Test inventory user with `07703333333`

### Creating Custom Test Scenarios

Edit your `seed_data.json` to add:
- More companies
- More users with different role combinations
- More products with varying stock levels
- Edge cases (inactive users, low stock products, etc.)

## Security Notes

**Important:**
- `seed_data.json` is gitignored - your credentials are safe
- `seed_data.example.json` is committed - only contains example/dummy data
- Never commit real passwords to the repository
- Use strong passwords for production environments

## Troubleshooting

### Error: Config file not found

```bash
cp seed_data.example.json seed_data.json
```

### Error: Invalid JSON

Validate your JSON:
```bash
python -m json.tool seed_data.json
```

### Error: Company not found for user/product

Make sure the `company_name` in users/products matches exactly with a company in the `companies` array.

### Database locked error (SQLite)

Make sure the backend server is not running when resetting the database:
- Stop the backend (Ctrl+C)
- Run reset script
- Start backend again

## Advanced Usage

### Custom Config File Location

```bash
python reset_database.py --config /path/to/my_custom_seed.json
```

### Partial Seeding

Edit `seed_data.json` to include only what you need:
- Remove `companies` array if you don't need sample companies
- Remove `users` array if you only need system admin
- Remove `products` array if you don't need sample products

The script will only seed what's present in the config.

## Help

View all options:
```bash
python reset_database.py --help
```
