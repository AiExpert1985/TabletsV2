# Database Setup

Simple database initialization for development.

## Quick Start

```bash
cd backend
python database_init/reset.py
```

**That's it!** No setup required.

## What It Does

- Drops all tables
- Creates fresh tables
- Loads test data from `.example.json` files
- Seeds database with sample companies, users, and products

## Default Login

After running the script, login with:

- **Phone:** `07700000000`
- **Password:** `Admin123`

## Full Documentation

See [database_init/README.md](database_init/README.md) for:
- Default test accounts
- Sample data details
- How to customize test data
