# Project Context - TabletsV2 ERP

> **📖 AI Assistant Onboarding**
>
> Read this file + `AI_GUIDELINES.md` at the start of each session:
> - **AI_GUIDELINES.md** - *How* to work (code style, tone, problem-solving)
> - **PROJECT_CONTEXT.md** (this file) - *What* exists and *why* (architecture, patterns, decisions)

---

## Quick Reference

| Category | Key Info |
|----------|----------|
| **Architecture** | 3-layer: Routes → Services → Repositories → Database |
| **Features** | auth, users, company, product, authorization, audit |
| **Auth** | Phone-first (+964), JWT, single refresh token per user |
| **Authorization** | Single-role RBAC (7 roles, 36 permissions) |
| **Multi-tenancy** | Single DB + company_id filtering via CompanyContext |
| **Testing** | 169 backend tests, 95+ client (100% pass rate) |
| **Database** | SQLite (dev), PostgreSQL (prod), async SQLAlchemy 2.0 |

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
- `audit/` - Comprehensive audit trail for tracking CRUD operations

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

### Authorization - Single-Role RBAC

**Design:** Each user has ONE role → ONE permission set (simpler than dual-role, easier to maintain)

**Roles:** `system_admin`, `company_admin`, `accountant`, `sales_manager`, `warehouse_keeper`, `salesperson`, `viewer`

**Usage Pattern:**
```python
from features.authorization.permission_checker import require_permission
from features.authorization.permissions import Permission

# Declarative permission checks in routes/services
require_permission(current_user, Permission.CREATE_PRODUCTS)
require_permission(current_user, Permission.CREATE_PRODUCTS, company_id=product.company_id)
```

**Available Functions:** `require_permission()`, `require_any_permission()`, `require_all_permissions()`, `require_system_admin()`, `require_company_admin()`

**Critical Security Checks:**
- ✅ Inactive users → Cannot login or pass permission checks
- ✅ Inactive companies → All employees blocked from login/permissions
- ✅ Company relationship eagerly loaded (prevents N+1, enables status validation)

**Location:** `features/authorization/` (permissions.py, role_permissions.py, permission_checker.py, service.py)

---

## Audit Trail System

**Purpose:** Track all CRUD operations for compliance, security, and troubleshooting

**Architecture:** Single `audit_logs` table (no audit fields on entities - simpler, survives deletions)

**What's Tracked:**
- WHO: user_id, username (`user.phone_number`), user_role
- WHEN: timestamp (UTC, indexed)
- WHERE: company_id, company_name (cached)
- WHAT: entity_type, entity_id, action (CREATE/UPDATE/DELETE)
- DETAILS: old_values, new_values, computed changes (JSON)

**Key Features:**
- Auto-filters sensitive data (passwords, tokens, secrets)
- Computes field-level changes for UPDATE actions
- Multi-tenancy aware (company admins see only their logs)
- Indexed for performance: `(company_id, timestamp)`, `(entity_type, entity_id)`

**Integration Pattern (Manual & Explicit):**
```python
class UserService:
    def __init__(self, repo: UserRepository, audit: AuditService):
        self.repo, self.audit = repo, audit

    async def create_user(..., current_user: User):
        user = await self.repo.save(...)
        if self.audit:
            await self.audit.log_create(
                user=current_user,
                entity_type="User",
                entity_id=str(user.id),
                values=user.dict(),
                company_id=user.company_id,
            )
        return user
```

**Integration Status:** UserService ✅ | CompanyService ⏳ | ProductService ⏳

**API Endpoints:**
- `GET /api/audit-logs` - Global audit log (admin only, filterable)
- `GET /api/audit-logs/{entity_type}/{entity_id}` - Entity history (all users)

**Location:** `features/audit/` | **Tests:** ~40 tests in `backend/tests/test_audit_*`

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

## Change Log (Recent Decisions)

### 2025-11-19: User Management UI & Audit Trail Fixes
- **UI:** Implemented create/edit user dialogs (FloatingActionButton + Edit menu item, full form validation)
- **Bug Fix:** Fixed `user.name` → `user.phone_number` in audit/service.py (3 occurrences)
- **Pattern:** Eager loading with `selectinload(User.company)` prevents MissingGreenlet errors
- **Files:** `user_management_screen.dart`, `audit/service.py`

### 2025-11-18: Audit Trail System
- **Added:** Comprehensive audit trail (single table, CREATE/UPDATE/DELETE tracking)
- **Features:** Sensitive data filtering, field-level changes, multi-tenancy, 2 API endpoints
- **Integration:** UserService ✅ | CompanyService ⏳ | ProductService ⏳
- **Tests:** ~40 tests covering repository, service, routes

### 2025-11-18: Single-Role RBAC Migration
- **Changed:** Dual-role → Single role field (simpler, 1:1 mapping)
- **Impact:** Expanded UserRole enum, updated backend/frontend, removed company_roles column
- **Benefits:** Easier to understand, test, and maintain

### 2025-11-18: Permission-Based Authorization
- **Pattern:** `require_permission(user, Permission.X)` instead of role checks
- **Benefits:** Self-documenting, centralized, testable, future-proof for dynamic roles

### 2025-11-18: Security - Inactive Users/Companies
- **Added:** Login blocks + permission checks for inactive users/companies
- **Implementation:** Enforced in AuthService.login() and AuthorizationService
- **Critical:** Company relationship eagerly loaded for status validation

### Key Architectural Decisions
- **Service Layer:** ALL business logic through services (never bypass)
- **Feature Split:** auth/ (authentication) + users/ (user CRUD) - one feature per capability
- **Dependencies:** Every feature MUST have dependencies.py (thin routes)
- **No Abstractions:** Removed ABC interfaces (YAGNI, duck typing for mocking)
- **3-Layer Pattern:** Routes → Services → Repositories → Database

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

**Last Updated:** 2025-11-19 (User management UI + audit trail fixes)
