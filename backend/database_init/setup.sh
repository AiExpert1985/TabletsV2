#!/bin/bash
# Setup seed data files for database initialization

echo "========================================"
echo "Database Initialization Setup"
echo "========================================"
echo

cd "$(dirname "$0")/data"

echo "Copying example files to actual data files..."
echo

cp system_admin.example.json system_admin.json && echo "[OK] system_admin.json" || echo "[FAIL] system_admin.json"
cp companies.example.json companies.json && echo "[OK] companies.json" || echo "[FAIL] companies.json"
cp users.example.json users.json && echo "[OK] users.json" || echo "[FAIL] users.json"
cp products.example.json products.json && echo "[OK] products.json" || echo "[FAIL] products.json"

echo
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo
echo "You can now run: python reset.py"
echo
