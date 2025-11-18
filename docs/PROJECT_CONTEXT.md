# Project Context - TabletsV2 ERP

> **📖 AI Assistant Onboarding Guide**
>
> This file, along with `AI_GUIDELINES.md`, contains **everything** an AI assistant needs to know about this project. Read both files at the start of each session to understand:
> - **AI_GUIDELINES.md** - *How* to work (tone, code style, problem-solving approach)
> - **PROJECT_CONTEXT.md** (this file) - *What* exists and *why* (architecture, decisions, patterns, trade-offs)
>
> These two files are the single source of truth. No other documentation files are needed for AI onboarding.

## Overview
Multi-tenant ERP system with FastAPI backend and Flutter client, following Clean Architecture principles with emphasis on simplicity and pragmatism.

---

## Architecture Decisions

### 1. Simplified Clean Architecture (3-Layer)
**Decision:** 3 layers instead of 4 (Presentation → Domain → Data)
**Rationale:** Services act as use cases; avoids over-engineering
**Trade-off:** Combined service/use-case layer for faster iteration while maintaining clean separation

**Backend:** `routes/ → services/ → repository/ → database`
**Client:** `screens/ → providers/ → services/ → repository/ → API`

### 2. Multi-Tenancy Strategy
**Implementation:** Single database with `company_id` filtering at application level
**System admin:** `company_id = NULL` (sees all companies)
**Company users:** Automatic filtering by their `company_id`
**How:** CompanyContext dependency injection + BaseRepository pattern

### 3. Repository Pattern (Concrete Classes Only)
**Decision:** No abstractions (ABC/Protocol) for repositories - use concrete classes directly
**Rationale:**
- YAGNI - Won't implement multiple repository backends
- Python's duck typing handles mocking without interfaces
- Reduces maintenance overhead (no interface/implementation sync)
- Consistent with service layer (no abstractions there either)
**Previous:** Used ABC (Abstract Base Classes), removed for pragmatism

### 4. Service Layer Design
**Decision:** Explicit service layer between providers and repositories
**Rationale:**
- Separates business logic from state management
- Easier to test (no state mocking)
- Mirrors backend architecture (consistency)

### 5. Type Safety Philosophy
**Backend:** Comprehensive type hints with Python 3.11+ syntax
**Client:** Sealed classes for state (AuthState, etc.) instead of enums
**Rationale:** Impossible states become impossible; compiler catches errors

---

## Flutter Client Patterns

### State Management: Sealed Classes (Not Enums)
**Critical:** Always use sealed classes for state, never enums.

```dart
// ✅ CORRECT
sealed class AuthState {}
class AuthStateLoading extends AuthState {}
class AuthStateAuthenticated extends AuthState {
  final User user;
  AuthStateAuthenticated(this.user);
}

// ❌ WRONG - Enums can't carry data
enum AuthStatus { loading, authenticated }
```

**Why:** Compiler enforces exhaustive pattern matching, each state carries its own data, impossible states become impossible.

### Riverpod Pattern
- **Flow:** `Screen → Provider → Service → Repository → API` (never skip layers)
- **Services:** Business logic only (phone normalization, validation)
- **Repositories:** Data access (API calls, storage)
- **Providers:** State management (StateNotifier with sealed class states)

### Error Handling
- Map technical errors to user-friendly messages in providers
- Exception hierarchy: `NetworkException`, `UnauthorizedException`, `ValidationException`
- Never expose technical error messages to users

### Models vs Entities
- **Pattern:** `UserModel extends User` (inheritance when API matches domain)
- **Why:** Pragmatic - avoids mapping boilerplate when structures align
- **When to separate:** If API and domain diverge significantly

### UI & Localization
- **Multi-language ready:** Design for English/Arabic (RTL/LTR) from start
- Use `EdgeInsets.symmetric` instead of left/right
- Use `Directionality.of(context)` for text direction

---

## Feature Status

### ✅ Completed
- **Auth:** Phone-first (+964 Iraqi numbers), bcrypt (cost 12), single refresh token per user
- **Multi-tenancy:** Company isolation via CompanyContext
- **Permissions:** 36 granular permissions + role-based aggregation (PermissionGroups class)
- **Products:** Basic CRUD operations
- **Testing:** 95+ client unit tests, 86+ backend tests (100% pass rate)
- **Database:** SQLite (dev) + PostgreSQL (prod) with GUID TypeDecorator for UUID consistency

### ❌ Deferred to Phase 2
- **Password Reset:** Removed insecure endpoints (was returning reset token in API response)
- **Rate Limiting:** In-memory (5 attempts/phone/hour) - needs Redis for production
- **Phone Validation:** Removed during development (server accepts any format)

---

## Critical Patterns & Conventions

### Authentication
- **Phone-first:** Iraqi phone numbers (+964) as primary identifier
- **Security:** Bcrypt (cost 12) + HMAC-SHA256 token hashing
- **Token strategy:** Single refresh token (logout other devices on new login)
- **No public signup:** Admin creation via CLI only (`scripts/admin/create_system_admin.py`)

### Permission System
- **Structure:** System roles (`system_admin`, `company_admin`, `user`) + company roles
- **Company roles:** admin, accountant, sales_manager, warehouse_keeper, salesperson, viewer
- **Innovation:** Type-safe `PermissionGroups` class instead of strings (prevents typos)

---

## Testing Strategy (80/20 Rule)

**Philosophy:** 70% effective coverage, not 100% actual coverage
**Focus:** Service layer > Repositories > Security > Endpoints

### Client Tests (95+ tests)
- ✅ Validators (phone, password) - 25+ tests
- ✅ JSON Models (serialization, roundtrip) - 35+ tests
- ✅ Auth Service (business logic, error handling) - 15+ tests
- ✅ Token Storage (persistence, security) - 20+ tests
- ⏭️ Skipped: Widgets, Providers (use integration tests)

### Backend Tests (86+ tests)
- ✅ Service layer (business logic)
- ✅ Repositories (data access)
- ✅ Security (auth, permissions)
- ✅ API endpoints
- **Tool:** pytest + async support, SQLite test DB with transaction rollback

**Key Insight:** Test critical business logic units, not framework internals or UI complexity.

> **🧪 Running Tests**
> For test commands, see [`README.md`](../README.md).

---

## Known Issues & Trade-offs

### 1. Phone Validation Removed
**Status:** Disabled during development
**Impact:** Server accepts any phone format
**Solution:** Add `libphonenumber` validation in production

### 2. UUID Format Inconsistency (Solved)
**Problem:** SQLite stored UUIDs without hyphens → 401 errors
**Solution:** Custom GUID TypeDecorator (SQLite: CHAR(36) with hyphens, PostgreSQL: native UUID)

### 3. Password Reset Deferred
**Problem:** Original plan returned reset token in API response (security hole)
**Solution:** Deferred to Phase 2; created abstraction (email/SMS interfaces)

### 4. Rate Limiting (In-Memory)
**Current:** In-memory rate limiter (5 attempts/phone/hour)
**Limitation:** Doesn't persist across restarts; won't work in multi-instance deployments
**Production:** Needs Redis

### 5. Service = Use Case Layer
**Decision:** Combined service and use case layers
**Trade-off:** Faster iteration vs theoretical purity
**Rationale:** Project is small enough that separation isn't needed yet

---

## Database Strategy

### Development vs Production
- **Development:** SQLite with async support (`aiosqlite`) - Zero setup, fast iteration
- **Production:** PostgreSQL with async support (`asyncpg`) - Robust, scalable
- **UUID handling:** Custom GUID TypeDecorator ensures consistent format across both databases

### Why SQLite for Development?
**Decision:** SQLite for dev, PostgreSQL for production
**Rationale:** Eliminates setup friction, allows instant database reset
**Trade-off:** Ensures compatibility layer works correctly (TypeDecorator pattern)

> **🛠️ Database Setup & Scripts**
> For database initialization, reset scripts, and seed data, see [`README.md`](../README.md).

---

## Development Philosophy

### Learning Strategy (For 40-year-old Developer with Limited Time)
- **70%** - Code you're modifying
- **20%** - Architecture/patterns
- **10%** - Everything else
- **Tests:** Use as safety net, not documentation (read only when they fail)
- **Focus:** Learn flows, not lines; patterns, not implementation details

### Code Quality Principles
- **Pragmatic over perfect:** Working solutions first
- **Junior-readable:** Clear variable names, obvious data flow
- **Fail fast:** Explicit errors, no silent catches
- **Testable by design:** Write code ready for testing
- **Standard patterns only:** Repository, Adapter, Strategy, Factory

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.115.0 + Uvicorn (async Python web framework)
- **Database:** SQLAlchemy 2.0 (async) + asyncpg/aiosqlite
- **Security:** PyJWT (tokens), bcrypt (password hashing)
- **Testing:** pytest + pytest-asyncio (NOT pytest-anyio - they conflict)
- **Config:** Dependencies in `pyproject.toml` (not `requirements.txt`)

### Client
- **Framework:** Flutter 3.x (cross-platform mobile)
- **State:** Riverpod (reactive state management)
- **HTTP:** Dio with interceptors (auth, logging)
- **Storage:** flutter_secure_storage (encrypted token persistence)
- **Testing:** mockito + build_runner (mocking framework)

> **🔧 Scripts & Installation**
> For setup scripts, dependencies installation, and utilities, see [`README.md`](../README.md).

---

## What to Preserve (Critical!)

### 1. Service Layer Architecture (MOST CRITICAL)
- **3-layer separation:** `routes/scripts → services → repositories → database`
- **NEVER bypass services:** ALL business operations MUST go through service layer
- **Pattern:** `await user_service.create_user(...)` ✅ NOT `User(...); repo.db.add()` ❌
- Routes and scripts are thin controllers - delegate to services
- Repository interfaces must be complete (declare ALL methods services use)
- Services = business logic only (no state management, no direct DB access)

### 2. Dependencies Organization (CRITICAL)
- **Every feature MUST have a `dependencies.py` file** for FastAPI dependencies
- **NEVER define dependencies in route files** - always move them to `dependencies.py`
- **Pattern:** Routes import from `dependencies.py`, never define `get_*_service()` locally
- **Example structure:**
  ```
  features/auth/
    ├── dependencies.py    # ✅ get_auth_service, get_user_service, build_user_response, etc.
    ├── auth_routes.py     # ✅ Imports from dependencies.py
    └── user_routes.py     # ✅ Imports from dependencies.py
  features/company/
    ├── dependencies.py    # ✅ get_company_service
    └── routes.py          # ✅ Imports from dependencies.py
  features/product/
    ├── dependencies.py    # ✅ get_product_service
    └── routes.py          # ✅ Imports from dependencies.py
  ```
- **What goes in `dependencies.py`:**
  - Service factory functions (`get_*_service`)
  - Authorization/permission checks (`require_system_admin`, etc.)
  - Response builders (`build_user_response`, etc.)
  - Error handlers (`handle_*_exception`)
  - Any reusable dependency used across multiple routes

### 3. Multi-Tenancy Isolation
- Never bypass `CompanyContext` filtering
- System admin: `company_id = NULL` (must handle explicitly)
- Always use `BaseRepository` for company-scoped entities
- **CompanyContext pattern:** `CompanyContext(user=user)` - `should_filter` is auto-calculated

### 4. Security
- No public signup - admin creation CLI-only (`scripts/db/create_admin.py`)
- Single refresh token per user (logout other devices on new login)
- Phone numbers are unique identifiers (not usernames)
- Bcrypt rounds = 12 (never lower for "performance")

### 5. Type Safety
- Backend: Always use type hints (Python 3.11+ syntax)
- Client: Always use sealed classes for state (not enums)
- Never use `dynamic` or `Any` unless absolutely necessary
- Use `TYPE_CHECKING` for circular import prevention

### 6. Testing
- 70% effective coverage, not 100% actual coverage
- Focus: Service layer > Repositories > Security > Endpoints
- Skip framework internals and UI widgets (use integration tests)

---

## AI Assistant Handoff Instructions

When starting a new feature or fixing a bug:

1. **Read this file first** - Understand architectural decisions and trade-offs
2. **Check Feature Status** - Don't re-implement deferred features
3. **Follow existing patterns** - Repository for data, Service for logic, sealed classes for state
4. **Preserve security** - Multi-tenancy isolation, no public signup, type safety
5. **Test strategically** - 70% effective coverage (services, validators, models)
6. **Update this file** - Add new architectural decisions or pattern changes at end of session

### When in Doubt
- ✅ Prefer simplicity over cleverness
- ✅ Follow existing conventions (check similar features)
- ✅ Ask user before major architectural changes
- ❌ Don't refactor working code "to make it better"
- ❌ Don't add dependencies without justification

---

## Documentation Strategy for AI Assistants

**Goal:** Minimize documentation sprawl - use the 3-file structure defined in AI_GUIDELINES.md.

### Where to Put Information

**When you need to document something, use this decision tree:**

1. **Operational/How-to-run info?** → **README.md**
   - Installation steps, setup commands, running tests
   - Scripts reference, API endpoints
   - Troubleshooting common issues
   - Example: Database setup commands, seed data credentials

2. **Architectural/Why decisions?** → **docs/PROJECT_CONTEXT.md**
   - Design patterns and rationale
   - Feature status (completed vs deferred)
   - Architectural trade-offs
   - Multi-tenancy design, testing philosophy
   - Example: Why we use ABC instead of Protocol for repositories

3. **Working style/Code standards?** → **docs/AI_GUIDELINES.md**
   - Code quality standards
   - Abstraction guidelines
   - Communication tone
   - Example: When to abstract, function length limits

4. **Implementation-level reference for specific feature?** → **Co-located guide** (ONLY if absolutely necessary)
   - Detailed usage patterns and code examples
   - Co-locate with the feature (e.g., `features/authorization/PERMISSIONS_GUIDE.md`)
   - Must provide significant value beyond code comments
   - Example: PERMISSIONS_GUIDE.md (type-safe permission patterns), COMPANY_ISOLATION_GUIDE.md (multi-tenancy patterns)

### Rules for AI Assistants

**❌ NEVER create:**
- New top-level documentation files
- Nested README files in subdirectories (except when truly needed for complex features)
- Duplicate information across multiple files

**✅ ALWAYS:**
- Check if information already exists in the 3 main docs
- Update existing documentation instead of creating new files
- Merge architectural insights into PROJECT_CONTEXT.md
- Merge operational info into main README.md
- Ask user before creating feature-specific guides

**Exception:** Feature-specific implementation guides (like PERMISSIONS_GUIDE.md or COMPANY_ISOLATION_GUIDE.md) are acceptable ONLY when:
- They provide detailed implementation patterns and code examples
- Information is too detailed for PROJECT_CONTEXT.md (would clutter it)
- They're co-located with the feature they document
- They serve as reference for developers working on that specific area

---

## Recent Changes & Sessions

### Session: Initial Setup
- Created 3-layer clean architecture (routes → services → repositories)
- Implemented multi-tenancy with company isolation via CompanyContext
- Set up phone-first authentication (+964 Iraqi numbers, bcrypt cost 12)
- Established testing strategy: 95+ client tests, 86+ backend tests

### Session: Project Reorganization
- Moved docs to `docs/` folder, consolidated scripts to `scripts/db/`
- Migrated dependencies to `pyproject.toml` (removed requirements.txt)
- Created PROJECT_CONTEXT.md and AI_GUIDELINES.md as single source of truth

### Session: Scripts & Type Safety (2025-11-17)
- **Scripts:** Consolidated all database scripts into `scripts/db/` folder (setup_all, reset_db, create_admin, seed_data)
- **Seed data:** Committed directly to git (no template pattern) - contains only sample data
- **Type safety:** Fixed Python 3.11+ compatibility (`TYPE_CHECKING`, `from __future__ import annotations`, TypeVar string literals)
- **Python version:** Minimum 3.11 (asyncpg 0.29.0 doesn't support 3.13 yet)

### Session: Service Layer Enforcement (2025-11-18)
- **Problem:** Routes/scripts bypassed services, accessed repositories directly (violated 3-layer architecture)
- **Solution:** Created UserService, ProductService, CompanyService; refactored ALL routes/scripts to use services
- **Pattern:** `await service.create_user(...)` ✅ NOT `User(...); repo.db.add()` ❌
- **Cleanup:** Removed unused signup code (auth/services.py → auth_services.py, routes.py → auth_routes.py for consistency)
- **Repository completeness:** Added missing methods to UserRepository (save, get_all, update, delete)
- **Tests:** Added 42 service layer tests (13 user, 15 product, 14 company)
- **Commits:** d1907c8, 99d72ab, 09f8ae2

### Session: Documentation Strategy (2025-11-18)
- **Change:** Added documentation strategy section to PROJECT_CONTEXT.md
- **Goal:** Prevent AI assistants from creating unnecessary documentation files
- **Decision tree:** README.md (operational), PROJECT_CONTEXT.md (architectural), AI_GUIDELINES.md (working style)
- **Cleanup:** Deleted client/README.md (useless Flutter boilerplate)
- **Exception:** Feature-specific guides allowed when co-located and providing detailed implementation patterns

### Session: Remove Repository Abstractions (2025-11-18)
- **Decision:** Removed all repository abstractions (IUserRepository, IRefreshTokenRepository, ICompanyRepository)
- **Rationale:** Pragmatic architecture - YAGNI principle, Python's duck typing handles mocking, reduces maintenance
- **Changes:**
  - Removed ABC interfaces from auth/repository.py, company/repository.py
  - Updated all services to use concrete repository types (UserRepository, RefreshTokenRepository, CompanyRepository)
  - Updated auth_services.py, user_service.py, company/service.py type hints
  - Tests continue to work - Mock() doesn't require ABC abstractions
- **Cleanup:** Removed unused `change_password()` method from UserService and `update_password()` from UserRepository
- **Pattern:** Consistent with service layer (no abstractions) - services and repositories are concrete classes only
- **Documentation:** Updated PROJECT_CONTEXT.md and AI_GUIDELINES.md to reflect no-abstraction policy

### Session: Dependencies Organization (2025-11-18)
- **Problem:** Dependencies scattered across route files instead of centralized `dependencies.py` files
- **Found scattered dependencies:**
  - auth_routes.py: `build_user_response()`, `handle_auth_exception()` (helper functions)
  - user_routes.py: `get_user_service()`, `require_system_admin()` (FastAPI dependencies)
  - company/routes.py: `get_company_service()` (FastAPI dependency)
  - product/routes.py: `get_product_service()` (FastAPI dependency)
- **Solution:**
  - Moved all auth dependencies to `features/auth/dependencies.py`
  - Created `features/company/dependencies.py` with `get_company_service()`
  - Created `features/product/dependencies.py` with `get_product_service()`
  - Updated all route files to import from `dependencies.py` instead of defining locally
- **Pattern:** Every feature MUST have a `dependencies.py` file - routes only import, never define
- **Documentation:** Added "Dependencies Organization" to PROJECT_CONTEXT.md "What to Preserve" section

---

**Last Updated:** 2025-11-18
