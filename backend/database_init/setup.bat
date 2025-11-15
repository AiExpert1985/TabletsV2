@echo off
REM Setup seed data files for database initialization

echo ========================================
echo Database Initialization Setup
echo ========================================
echo.

cd /d "%~dp0data"

echo Copying example files to actual data files...
echo.

copy /Y system_admin.example.json system_admin.json
if %ERRORLEVEL% EQU 0 (
    echo [OK] system_admin.json
) else (
    echo [FAIL] system_admin.json
)

copy /Y companies.example.json companies.json
if %ERRORLEVEL% EQU 0 (
    echo [OK] companies.json
) else (
    echo [FAIL] companies.json
)

copy /Y users.example.json users.json
if %ERRORLEVEL% EQU 0 (
    echo [OK] users.json
) else (
    echo [FAIL] users.json
)

copy /Y products.example.json products.json
if %ERRORLEVEL% EQU 0 (
    echo [OK] products.json
) else (
    echo [FAIL] products.json
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run: python reset.py
echo.
pause
