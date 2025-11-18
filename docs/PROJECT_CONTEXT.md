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
- **Security:** Phone-first auth (+964), bcrypt, JWT, single refresh token per user
- **Tests:** 114 backend tests, 95+ client tests (100% pass rate)

---

## Core Architecture (CRITICAL!)

### 1. Service Layer Pattern (MOST IMPORTANT)
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
  ├── schemas.py         # Request/response DTOs
  └── {feature}_guide.md # Optional: detailed patterns (if needed)
```

**Current Features:**
- `auth/` - Authentication (login, tokens, /auth/me) - **owns User model**
- `users/` - User management CRUD + UserRepository - system admin only
- `company/` - Company management - system admin only
- `product/` - Product CRUD with multi-tenancy
- `authorization/` - Permission system (36 granular permissions + permission checker)

**Dependency Flow:** `users → auth` (one-way, clean)

**Repository Organization:**
- `auth/repository.py` - RefreshTokenRepository only
- `users/repository.py` - UserRepository (user CRUD belongs with user management)

### 3. Dependencies Organization
**Every feature MUST have `dependencies.py`** containing:
- Service factories (`get_*_service`)
- Auth checks (`require_system_admin`)
- Response builders (`build_user_response`)
- Error handlers (`handle_*_exception`)

❌ **NEVER** define these in route files - always import from `dependencies.py`

### 4. Multi-Tenancy Isolation
**Implementation:** Single database + `company_id` filtering

**Rules:**
- System admin: `company_id = NULL` (sees all)
- Company users: Automatic filtering by `company_id`
- Use `CompanyContext` dependency injection
- Use `BaseRepository` for company-scoped entities
- **NEVER** bypass CompanyContext filtering

### 5. Type Safety & Patterns
**Backend:**
- Python 3.11+ type hints (required)
- Concrete repository classes (no ABC - duck typing for mocking)
- No abstractions for services or repositories (YAGNI)

**Client:**
- Sealed classes for state (not enums - they can't carry data)
- Flow: `Screen → Provider → Service → Repository → API`

---

## Security & Authentication

**Critical Rules:**
- ✅ Phone-first auth (+964 Iraqi numbers)
- ✅ Bcrypt cost 12 (never lower!)
- ✅ Single refresh token per user (logout others on login)
- ✅ No public signup - admin CLI only (`scripts/db/create_admin.py`)
- ✅ Phone numbers = unique identifiers

**Permissions:**
- System roles: `system_admin`, `company_admin`, `user`
- Company roles: admin, accountant, sales_manager, warehouse_keeper, salesperson, viewer
- Type-safe `PermissionGroups` class (prevents typos)

### 6. Permission-Based Authorization (NEW!)

**Pattern:** Permission-based access control with centralized checking

**Why:** Prepares for future dynamic roles while keeping current hardcoded mappings simple.

**Implementation:**
```python
# In routes/services - declarative permission checks
from features.authorization.permission_checker import require_permission
from features.authorization.permissions import Permission

require_permission(current_user, Permission.CREATE_PRODUCTS)
require_permission(current_user, Permission.CREATE_PRODUCTS, company_id=product.company_id)
```

**Benefits:**
- ✅ Self-documenting - clear what permission each endpoint needs
- ✅ Centralized logic - all authorization in one place
- ✅ Easy testing - test permission checker once, not role combinations
- ✅ Future-proof - can migrate to dynamic roles without changing endpoints

**Available Functions:**
- `require_permission(user, perm, company_id?)` - Main authorization check
- `require_any_permission(user, [perms], company_id?)` - OR logic
- `require_all_permissions(user, [perms], company_id?)` - AND logic
- `require_system_admin(user)` - System admin only
- `require_company_admin(user)` - Admin only (system or company)

**Location:** `features/authorization/permission_checker.py`

**Migration Path:**
- Current: Hardcoded role → permission mapping in `role_permissions.py`
- Future: Can move mappings to database without changing endpoints
- Endpoints only care about permissions, not roles

---

## Testing Strategy

**Philosophy:** 70% effective coverage, not 100% actual coverage

**Focus Areas:**
1. Service layer (business logic) - HIGHEST priority
2. Repositories (data access)
3. Security (auth, permissions)
4. Validators & models

**Skip:** Framework internals, UI widgets (use integration tests)

**Tools:** pytest + pytest-asyncio (backend), mockito (client)

> **Running Tests:** See `README.md`

---

## Database Strategy

**Development:** SQLite (aiosqlite) - zero setup, fast iteration
**Production:** PostgreSQL (asyncpg) - robust, scalable
**UUID Handling:** Custom GUID TypeDecorator (consistent format across DBs)

**Seed Data:**
- `scripts/db/seed_data.py` - Sample companies, users, products
- Committed to git (not templates)
- Credentials documented in README.md

> **DB Commands:** See `README.md`

---

## Known Trade-offs & Issues

### 1. Simplified Architecture
- **Decision:** Combined service/use-case layer (3 layers instead of 4)
- **Why:** Project small enough; faster iteration
- **Trade-off:** Less theoretical purity, more pragmatism

### 2. No Repository Abstractions
- **Decision:** Concrete classes only (removed ABC)
- **Why:** YAGNI - won't swap repository backends; Python duck typing handles mocking
- **Trade-off:** Less "textbook" but simpler maintenance

### 3. Rate Limiting (In-Memory)
- **Status:** In-memory (5 attempts/phone/hour)
- **Limitation:** Doesn't persist, won't work with multiple instances
- **Production:** Needs Redis

### 4. Phone Validation Disabled
- **Status:** Removed during development
- **Impact:** Server accepts any phone format
- **Production:** Add `libphonenumber` validation

### 5. UUID Format (SOLVED)
- **Problem:** SQLite stored UUIDs without hyphens → 401 errors
- **Solution:** GUID TypeDecorator (hyphens in both SQLite/PostgreSQL)

---

## Flutter Client Patterns

### State Management - Sealed Classes (NOT Enums!)
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

**Why:** Compiler enforces exhaustive matching, states carry data

### Riverpod Flow
`Screen → Provider → Service → Repository → API` (never skip layers)

### Multi-Language Ready
- Design for English/Arabic (RTL/LTR)
- Use `EdgeInsets.symmetric` (not left/right)
- Use `Directionality.of(context)`

---

## Documentation Strategy

**3-File Structure:**
1. **README.md** - Operational (setup, scripts, running tests)
2. **PROJECT_CONTEXT.md** - Architectural (patterns, decisions, why)
3. **AI_GUIDELINES.md** - Working style (tone, code standards)

**Rules for AI Assistants:**
- ❌ Don't create new top-level docs
- ❌ Don't duplicate information
- ✅ Update existing docs
- ✅ Ask before creating feature-specific guides

**Exception:** Feature guides allowed if:
- Co-located with feature
- Detailed implementation patterns
- Too detailed for PROJECT_CONTEXT.md

**Examples:** `PERMISSIONS_GUIDE.md`, `COMPANY_ISOLATION_GUIDE.md`

---

## AI Assistant Handoff

**Starting a new task:**
1. Read PROJECT_CONTEXT.md + AI_GUIDELINES.md
2. Check "Current Features" - don't re-implement
3. Follow existing patterns
4. Preserve security & multi-tenancy
5. Test strategically (70% effective coverage)
6. Update docs with new architectural decisions

**When in doubt:**
- ✅ Prefer simplicity over cleverness
- ✅ Follow existing conventions
- ✅ Ask before major architectural changes
- ❌ Don't refactor working code "to make it better"

---

## Change Log (Key Decisions)

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
- **Change:** Removed IUserRepository, IRefreshTokenRepository, ICompanyRepository (ABC)
- **Why:** YAGNI + Python duck typing handles mocking
- **Impact:** Simpler, less maintenance overhead

### 2025-11-18: Service Layer Enforcement
- **Change:** Created UserService, ProductService, CompanyService
- **Why:** Routes/scripts were bypassing service layer
- **Rule:** ALL business logic through services (never User(...); repo.db.add())

### 2025-11-17: Type Safety & Scripts
- **Change:** Python 3.11+ type hints, consolidated scripts to `scripts/db/`
- **Why:** Type safety + better organization

### Initial: 3-Layer Architecture
- **Decision:** `routes → services → repositories → database`
- **Why:** Pragmatic clean architecture (3 layers, not 4)
- **Trade-off:** Combined service/use-case for faster iteration

---

**Last Updated:** 2025-11-18 (Permission-based authorization + UserRepository reorganization)
