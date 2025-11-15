# Database Setup and Reset

**MOVED:** Database initialization has been reorganized.

Please see **[database_init/README.md](database_init/README.md)** for complete documentation.

## Quick Start

```bash
# First time setup
cd database_init/data
cp system_admin.example.json system_admin.json
cp companies.example.json companies.json
cp users.example.json users.json
cp products.example.json products.json

# Reset and seed database
cd ..
python database_init/reset.py
```

## What Changed

The database initialization has been reorganized for better maintainability:

**Old Structure:**
- `reset_database.py` - Script with embedded data
- `seed_data.example.json` - All data in one file
- `create_system_admin.py` - Separate admin script

**New Structure:**
```
database_init/
├── reset.py          # Main script
├── operations.py     # Database operations (code only)
├── data/             # All seed data
│   ├── system_admin.json
│   ├── companies.json
│   ├── users.json
│   └── products.json
└── README.md         # Full documentation
```

**Benefits:**
- ✅ Clear separation of code and data
- ✅ Easy to customize each entity type
- ✅ Modular - add/remove data files as needed
- ✅ Better organization for team collaboration

## See Also

- [database_init/README.md](database_init/README.md) - Full documentation
- [database_init/data/](database_init/data/) - Seed data files

## Old Files

The following files are deprecated and will be removed:
- `reset_database.py` (use `database_init/reset.py` instead)
- `seed_data.example.json` (use files in `database_init/data/` instead)
- `create_system_admin.py` (use `database_init/reset.py` instead)
