# Project Context - TabletsV2 ERP

> **📖 AI Assistant Onboarding**
>
> Read this file + `AI_GUIDELINES.md` at the start of each session:
> - **AI_GUIDELINES.md** - *How* to work (code style, tone, problem-solving)
> - **PROJECT_CONTEXT.md** (this file) - *What* exists and *why* (architecture, patterns, decisions)

---

## Overview

**Multi-tenant ERP system** - FastAPI backend + Flutter client, following pragmatic clean architecture.

**Tech Stack:**
- **Backend:** FastAPI 0.115 + SQLAlchemy 2.0 (async) + SQLite/PostgreSQL
- **Client:** Flutter 3.x + Riverpod + Dio
- **Security:** Phone-first auth (+964), bcrypt, JWT, single-role RBAC
- **Tests:** 169 backend tests, 95+ client tests (100% pass rate)

---

## Core Architecture Patterns

### 1. Service Layer Pattern ⭐ MOST IMPORTANT
**3-layer separation:** `routes/scripts → services → repositories → database`

**Rules:**
- ✅ `await user_service.create_user(...)` - ALL business logic through services
- ❌ `User(...); repo.db.add()` - NEVER bypass service layer
- Routes are thin controllers - delegate everything to services
- Services = pure business logic (no DB, no state)

### 2. Feature Organization
**Pattern:** One feature per business capability, one feature per UI screen

**Structure:**
```
features/{feature_name}/
  ├── models.py          # Database models (if feature owns data)
  ├── repository.py      # Data access (concrete classes, no ABC)
  ├── service.py         # Business logic
  ├── routes.py          # HTTP endpoints
  ├── dependencies.py    # FastAPI dependencies (REQUIRED)
  └── schemas.py         # Request/response DTOs
```

**Current Features:**
- `auth/` - Authentication (login, tokens, /auth/me) - **owns User model**
- `users/` - User management CRUD + UserRepository - admin only
- `company/` - Company management - admin only
- `product/` - Product CRUD with multi-tenancy
- `authorization/` - Single-role permission system (7 roles, 36 permissions)

**Key Rule:** Every feature MUST have `dependencies.py` - never define dependencies in route files

### 3. Multi-Tenancy Isolation
**Implementation:** Single database + `company_id` filtering via `CompanyContext`

**Rules:**
- System admin: `company_id = NULL` (sees all)
- Company users: Automatic filtering by their `company_id`
- Use `BaseRepository` for company-scoped entities
- **NEVER** bypass CompanyContext filtering

### 4. Type Safety
- Python 3.11+ type hints (required)
- Concrete repository classes (no ABC - YAGNI + duck typing for mocking)
- Client: Sealed classes for state (not enums - they can't carry data)

---

## Security & Authorization

### Authentication
**Critical Rules:**
- ✅ Phone-first auth (+964 Iraqi numbers only)
- ✅ Bcrypt cost 12 (never lower!)
- ✅ Single refresh token per user (logout others on login)
- ✅ No public signup - admin CLI only (`scripts/db/create_admin.py`)
- ✅ Phone numbers = unique identifiers

### Authorization - Single-Role System

**Design:** Each user has ONE role that maps to a permission set.

**Roles (UserRole enum):**
- `system_admin` - Full access to all companies
- `company_admin` - Full access within their company
- `accountant` - Financial operations & reports
- `sales_manager` - Manage sales & salespeople
- `warehouse_keeper` - Inventory & warehouse operations
- `salesperson` - Create invoices, view products
- `viewer` - Read-only access

**Why Single-Role:**
- ✅ Simpler than dual-role (system_role + company_roles)
- ✅ Easier to explain to clients
- ✅ Less complex to test and maintain
- ✅ Direct mapping: 1 role = 1 permission set

**Permission-Based Access Control:**
```python
# In routes/services - declarative permission checks
from features.authorization.permission_checker import require_permission
from features.authorization.permissions import Permission

require_permission(current_user, Permission.CREATE_PRODUCTS)
require_permission(current_user, Permission.CREATE_PRODUCTS, company_id=product.company_id)
```

**Available Functions:**
- `require_permission(user, perm, company_id?)` - Main authorization check
- `require_any_permission(user, [perms], company_id?)` - OR logic
- `require_all_permissions(user, [perms], company_id?)` - AND logic
- `require_system_admin(user)` - System admin only
- `require_company_admin(user)` - Admin only (system or company)

**Security Checks (CRITICAL):**
1. ✅ **Inactive users** cannot login or pass any permission checks
2. ✅ **Inactive companies** - all employees cannot login or pass permissions
3. ✅ Checks enforced in both `AuthService.login()` and `AuthorizationService._calculate_permissions()`
4. ✅ Company relationship eagerly loaded for status validation

**Benefits:**
- Self-documenting - clear what permission each endpoint needs
- Centralized logic - all authorization in one place
- Easy testing - test permission checker once, not role combinations
- Future-proof - can migrate to dynamic roles without changing endpoints

**Location:** `features/authorization/`
- `permissions.py` - Permission enum + PermissionGroups
- `role_permissions.py` - Role → Permission mappings (hardcoded)
- `permission_checker.py` - Authorization functions
- `service.py` - AuthorizationService (permission calculation)

---

## Testing Strategy

**Philosophy:** 70% effective coverage, not 100% actual coverage

**Focus Areas:**
1. Service layer (business logic) - HIGHEST priority
2. Repositories (data access)
3. Security (auth, permissions, inactive users/companies)
4. Validators & models

**Skip:** Framework internals, UI widgets (use integration tests)

**Tools:** pytest + pytest-asyncio (backend), mockito (client)

---

## Database Strategy

**Development:** SQLite (aiosqlite) - zero setup, fast iteration
**Production:** PostgreSQL (asyncpg) - robust, scalable
**UUID Handling:** Custom GUID TypeDecorator (consistent format across DBs)

**Seed Data:**
- `scripts/db/seed_data.py` + `seed_data.json` - Sample companies, users, products
- Committed to git (not templates)
- Uses single-role system (roles: `company_admin`, `salesperson`, `warehouse_keeper`, `accountant`)

---

## Flutter Client Patterns

### State Management - Sealed Classes (NOT Enums!)
```dart
// ✅ CORRECT - Sealed classes carry data
sealed class AuthState {}
class AuthStateLoading extends AuthState {}
class AuthStateAuthenticated extends AuthState {
  final User user;
  AuthStateAuthenticated(this.user);
}

// ❌ WRONG - Enums can't carry data
enum AuthStatus { loading, authenticated }
```

**Why:** Compiler enforces exhaustive matching, states carry data

### Riverpod Flow
`Screen → Provider → Service → Repository → API` (never skip layers)

### Multi-Language Ready
- Design for English/Arabic (RTL/LTR)
- Use `EdgeInsets.symmetric` (not left/right)
- Use `Directionality.of(context)`

### User Model (matches backend)
- Single `role` field (string): `"system_admin"`, `"company_admin"`, `"accountant"`, etc.
- No `companyRoles` field (removed)
- `UserRole` constants class for type-safe role references

---

## Known Trade-offs

### 1. Simplified Architecture
- **Decision:** Combined service/use-case layer (3 layers instead of 4)
- **Why:** Project small enough; faster iteration
- **Trade-off:** Less theoretical purity, more pragmatism

### 2. No Repository Abstractions
- **Decision:** Concrete classes only (no ABC)
- **Why:** YAGNI - won't swap backends; Python duck typing handles mocking
- **Trade-off:** Less "textbook" but simpler maintenance

### 3. Rate Limiting (In-Memory)
- **Status:** In-memory (5 attempts/phone/hour)
- **Limitation:** Doesn't persist, won't work with multiple instances
- **Production:** Needs Redis

### 4. Phone Validation Disabled
- **Status:** Removed during development
- **Impact:** Server accepts any phone format
- **Production:** Add `libphonenumber` validation

---

## Documentation Strategy

**3-File Structure:**
1. **README.md** - Operational (setup, scripts, running tests)
2. **PROJECT_CONTEXT.md** (this file) - Architectural (patterns, decisions, why)
3. **AI_GUIDELINES.md** - Working style (tone, code standards)

**Rules for AI Assistants:**
- ❌ Don't create new top-level docs
- ❌ Don't duplicate information
- ✅ Update existing docs with architectural decisions
- ✅ Feature-specific guides allowed (co-located, detailed patterns only)

---

## Change Log (Key Decisions)

### 2025-11-18: Single-Role System Migration
- **Change:** Removed dual-role system (system_role + company_roles), replaced with single `role` field
- **Why:** Simpler to understand, test, and explain to clients; reduced complexity
- **Migration:** Expanded UserRole enum with all role types (ACCOUNTANT, SALES_MANAGER, WAREHOUSE_KEEPER, SALESPERSON, VIEWER)
- **Impact:**
  - Backend: Updated User model, AuthorizationService, all tests (169 passing)
  - Frontend: Updated User entity, UserModel, all tests, added UserRole constants
  - Database: Removed company_roles column, updated seed data
- **Benefits:** Direct 1:1 mapping (role → permission set), easier maintenance

### 2025-11-18: Security Checks for Inactive Users/Companies
- **Change:** Added security checks for inactive users and inactive companies
- **Why:** Critical security requirement to prevent access from deactivated accounts
- **Implementation:**
  - Login blocks inactive users and users from inactive companies
  - Permission system returns empty set for inactive users/companies
  - Company relationship eagerly loaded for efficient status checks
- **Tests:** Added comprehensive tests for both scenarios (all passing)

### 2025-11-18: Permission-Based Authorization
- **Change:** Created centralized `permission_checker.py` for authorization
- **Why:** Prepare for dynamic roles, make code more maintainable and testable
- **Pattern:** `require_permission(user, Permission.CREATE_PRODUCTS)` instead of role checks
- **Benefits:** Self-documenting endpoints, centralized logic, easy testing, future-proof

### 2025-11-18: UserRepository Moved to users/
- **Change:** Moved `UserRepository` from `auth/repository.py` to `users/repository.py`
- **Why:** User CRUD belongs with user management, not authentication
- **Impact:** `auth/` now only has RefreshTokenRepository (authentication-specific)

### 2025-11-18: Auth/Users Feature Split
- **Change:** Split `features/auth/` into `auth/` (authentication) + `users/` (user management)
- **Why:** Align with UI (separate screens), clear responsibilities
- **Pattern:** One feature per business capability

### 2025-11-18: Dependencies Organization
- **Change:** Centralized all dependencies into `{feature}/dependencies.py`
- **Why:** Routes should be thin, dependencies reusable
- **Rule:** Every feature MUST have dependencies.py

### 2025-11-18: Repository Abstractions Removed
- **Change:** Removed ABC interfaces (IUserRepository, IRefreshTokenRepository, ICompanyRepository)
- **Why:** YAGNI + Python duck typing handles mocking
- **Impact:** Simpler, less maintenance overhead

### 2025-11-18: Service Layer Enforcement
- **Change:** Created UserService, ProductService, CompanyService
- **Why:** Routes/scripts were bypassing service layer
- **Rule:** ALL business logic through services (never `User(...); repo.db.add()`)

### Initial: 3-Layer Architecture
- **Decision:** `routes → services → repositories → database`
- **Why:** Pragmatic clean architecture (3 layers, not 4)
- **Trade-off:** Combined service/use-case for faster iteration

---

## AI Assistant Handoff

**Starting a new task:**
1. Read PROJECT_CONTEXT.md + AI_GUIDELINES.md
2. Check "Current Features" - don't re-implement
3. Follow existing patterns (service layer, single-role, permission-based auth)
4. Preserve security (inactive checks) & multi-tenancy
5. Test strategically (70% effective coverage)
6. Update docs with new architectural decisions

**When in doubt:**
- ✅ Prefer simplicity over cleverness
- ✅ Follow existing conventions
- ✅ Ask before major architectural changes
- ❌ Don't refactor working code "to make it better"

---

**Last Updated:** 2025-11-18 (Single-role system + security checks for inactive users/companies)
