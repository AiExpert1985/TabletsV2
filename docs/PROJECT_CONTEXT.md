# Project Context - TabletsV2 ERP

> **📖 AI Assistant Onboarding**
>
> Read this + `AI_GUIDELINES.md` at session start:
> - **AI_GUIDELINES.md** - *How* to work (style, tone, process)
> - **PROJECT_CONTEXT.md** (this) - *What* exists and *why* (architecture, decisions)

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

**Stack:** FastAPI + SQLAlchemy 2.0 (async) + Flutter + Riverpod
**Auth:** Phone (+964) + bcrypt + JWT + single-role RBAC
**Tests:** 169 backend, 95+ client (100% pass)
**Features:** Auth, Users, Companies, Products, Authorization

---

## Critical Patterns ⭐

### 1. Service Layer (MOST IMPORTANT)
**Rule:** ALL business logic through services - NEVER bypass

```python
# ✅ CORRECT
await user_service.create_user(...)

# ❌ WRONG - bypasses validation
User(...); repo.db.add()
```

**Flow:** `routes/scripts → services → repositories → database`

### 2. Feature Organization
**Pattern:** One feature per business capability

```
features/{feature_name}/
  ├── models.py          # DB models (if owns data)
  ├── repository.py      # Data access
  ├── service.py         # Business logic
  ├── routes.py          # HTTP endpoints
  ├── dependencies.py    # FastAPI deps (REQUIRED)
  └── schemas.py         # Request/response DTOs
```

**Features:**
- `auth/` - Authentication (login, tokens) - owns User model
- `users/` - User CRUD - system admin only
- `company/` - Company CRUD - system admin only
- `product/` - Product CRUD with multi-tenancy
- `authorization/` - Single-role permission system (7 roles, 36 permissions)
- `audit/` - Comprehensive audit trail for tracking CRUD operations

**Roles:** system_admin, company_admin, accountant, sales_manager, warehouse_keeper, salesperson, viewer

**Security:**
- ✅ Inactive users → no access
- ✅ Inactive companies → all employees no access
- ✅ Checks in login + permission calculation
- ✅ Company relationship eagerly loaded

**Location:** `features/authorization/`
- `permissions.py` - Permission enum (36 permissions)
- `role_permissions.py` - Role → Permissions mapping
- `permission_checker.py` - Authorization functions
- `service.py` - Permission calculation logic

### 4. Multi-Tenancy
**Pattern:** Single DB + `company_id` filtering via `CompanyContext`

- System admin: `company_id = NULL` (sees all)
- Company users: Auto-filtered by their `company_id`
- Use `BaseRepository` for scoped entities

### 5. SQLAlchemy Eager Loading (CRITICAL)
**Problem:** Accessing relationships outside async context → MissingGreenlet error

**Solution:** Eagerly load relationships in all repository methods

```python
# ✅ CORRECT - Eager load
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(User)
    .where(User.id == user_id)
    .options(selectinload(User.company))  # Load relationship
)
return result.scalar_one()

# ❌ WRONG - Lazy load (fails when accessed later)
await db.refresh(user)  # Doesn't load relationships
```

**Apply to:** get_by_id, get_all, create, save, update methods

---

## Flutter Client Patterns

### Clean Architecture (CRITICAL)
**Flow:** `Screen → Provider → Service → Repository → DataSource → API`

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

// Conditional UI elements
if (PermissionChecker.hasPermission(user, Permission.deleteUsers)) {
  IconButton(onPressed: () => deleteUser(), icon: Icon(Icons.delete))
}
```

**Client Implementation:**
- `core/authorization/permissions.dart` - Permission enum (28 permissions)
- `core/authorization/role_permissions.dart` - Role → Permissions
- `core/authorization/permission_checker.dart` - Check functions

### Reference Data Pattern (Dropdowns)
**Pattern:** FutureProvider for reference data + Consumer for loading states

```dart
// Provider
final companiesProvider = FutureProvider<List<Company>>((ref) async {
  final dataSource = ref.watch(companyDataSourceProvider);
  return dataSource.getCompanies();
});

// UI - Use Consumer for loading/error/data states
Consumer(
  builder: (context, ref, child) {
    final companiesAsync = ref.watch(companiesProvider);
    return companiesAsync.when(
      data: (companies) => DropdownButton(...),
      loading: () => CircularProgressIndicator(),
      error: (e, _) => Text('Error: $e'),
    );
  },
)
```

**Benefits:** Automatic caching, loading states, error handling

### Testing StateNotifier
**Pattern:** Test final state directly (not listeners)

```dart
// ✅ CORRECT - Check final state
await notifier.getUsers();
expect(notifier.state, isA<UsersLoaded>());

// ❌ WRONG - Listener doesn't capture initial state
final states = <UserState>[];
notifier.addListener((state) => states.add(state));
await notifier.getUsers();
expect(states[0], isA<UserLoading>());  // Fails!
```

---

## Security Rules (NON-NEGOTIABLE)

1. ✅ Phone-first auth (+964 Iraqi numbers)
2. ✅ Bcrypt cost 12 (never lower)
3. ✅ Single refresh token per user (logout others on login)
4. ✅ No public signup - admin CLI only
5. ✅ Inactive users cannot login or pass permission checks
6. ✅ Inactive companies block all employees
7. ✅ Permission checks include company_id validation
8. ✅ Company relationships eagerly loaded for status checks

---

## Testing Strategy

**Philosophy:** 70% effective coverage (not 100% actual)

**Priority:**
1. Service layer (business logic) - HIGH
2. Repositories (data access) - HIGH
3. Security (auth, permissions, inactive checks) - HIGH
4. Authorization (permission calculations) - HIGH
5. Validators & models - MEDIUM
6. Routes/integration - MEDIUM
7. UI/widgets - LOW (use integration tests)

**Tools:** pytest + pytest-asyncio (backend), mockito (client)

---

## Database

**Dev:** SQLite (aiosqlite)
**Prod:** PostgreSQL (asyncpg)
**UUIDs:** Custom GUID TypeDecorator (cross-DB consistency)

**Seed Data:** `scripts/db/seed_data.py` + `seed_data.json` (committed)

---

## Known Trade-offs

### 1. Simplified Architecture
- **What:** 3 layers (routes → services → repos), not 4
- **Why:** Project size doesn't justify extra layer
- **Trade-off:** Less theoretical purity, more pragmatism

### 2. No Repository Abstractions
- **What:** Concrete classes (no ABC interfaces)
- **Why:** YAGNI + Python duck typing for mocking
- **Trade-off:** Less "textbook", simpler code

### 3. Rate Limiting
- **Status:** In-memory (5 attempts/phone/hour)
- **Production:** Needs Redis for multi-instance

### 4. Phone Validation
- **Status:** Disabled during development
- **Production:** Add libphonenumber validation

---

## Change Log (Recent)

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

## AI Assistant Checklist

**Starting a session:**
1. ✅ Read PROJECT_CONTEXT.md + AI_GUIDELINES.md
2. ✅ Check "Features" - don't re-implement
3. ✅ Follow patterns: service layer, single-role, permission-based
4. ✅ Preserve security (inactive checks, eager loading)
5. ✅ Test strategically (70% effective coverage)
6. ✅ Update docs with architectural decisions

**Key Rules:**
- ✅ Prefer simplicity over cleverness
- ✅ Follow existing conventions
- ✅ Ask before major changes
- ❌ Don't refactor working code "for improvement"

---

**Last Updated:** 2025-11-19 (User management UI + audit trail fixes)
