# Project Context - TabletsV2 ERP

## Quick Reference

**Stack:** FastAPI + SQLAlchemy 2.0 (async) + Flutter + Riverpod
**Auth:** Phone (+964) + bcrypt + JWT + single-role RBAC
**Tests:** 169 backend, 95+ client (100% pass)
**Architecture:** Service layer + Feature-based + Core modules (shared types)
**Features:** Auth, Users, Companies, Products, Authorization
**Database:** SQLite (dev) → PostgreSQL (prod) with cross-DB type decorators

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

**Core Modules:** (Shared across features)
- `core/models.py` - SQLAlchemy type decorators (UUID, JSONList)
- `core/enums.py` - Shared enums (UserRole)
- `core/exceptions.py` - Custom exception types

**Features:**
- `auth/` - Authentication (login, tokens, RefreshToken model)
- `users/` - User CRUD + User model (system admin only)
- `company/` - Company CRUD - system admin only
- `product/` - Product CRUD with multi-tenancy
- `authorization/` - Permission system (7 roles, 36 permissions)

### 3. Core Modules (Shared Code)
**Pattern:** Shared types, enums, and utilities in `core/` directory

**Purpose:**
- Avoid circular dependencies between features
- Provide consistent cross-database types (UUID, JSONList)
- Share enums used by multiple features (UserRole)

**Key Modules:**
```python
# core/models.py - SQLAlchemy type decorators
class UUID(TypeDecorator):
    """Cross-DB UUID type (PostgreSQL UUID or SQLite CHAR(36))"""
    impl = String(36)
    cache_ok = True

class JSONList(TypeDecorator):
    """Cross-DB JSON list type"""
    impl = Text
    cache_ok = True

# core/enums.py - Shared enums
class UserRole(str, enum.Enum):
    SYSTEM_ADMIN = "system_admin"
    COMPANY_ADMIN = "company_admin"
    # ... other roles
```

**Rule:** Only shared, stable types go in `core/`. Feature-specific models stay in their features.

### 4. Single-Role Authorization
**Each user = ONE role → ONE permission set**

```python
# Declarative permission checks
require_permission(user, Permission.CREATE_PRODUCTS)
require_permission(user, Permission.VIEW_INVOICES, company_id=invoice.company_id)
```

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

### 5. Multi-Tenancy
**Pattern:** Single DB + `company_id` filtering via `CompanyContext`

- System admin: `company_id = NULL` (sees all)
- Company users: Auto-filtered by their `company_id`
- Use `BaseRepository` for scoped entities

### 6. SQLAlchemy Eager Loading (CRITICAL)
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

**RULE:** Every feature MUST have a service layer. Providers NEVER call repositories directly.

```
features/{feature_name}/
  ├── data/
  │   ├── datasources/       # API calls
  │   ├── models/            # DTOs
  │   └── repositories/      # Repository impl
  ├── domain/
  │   ├── entities/          # Domain models
  │   ├── repositories/      # Repository interface
  │   └── services/          # Business logic (REQUIRED)
  └── presentation/
      ├── providers/         # Riverpod StateNotifier
      ├── screens/           # UI screens
      └── widgets/           # Reusable components
```

**Service Layer Responsibilities:**
- Business logic and validation
- Data normalization (e.g., phone numbers)
- Error mapping (technical → user-friendly messages)
- DTO creation and manipulation
- Single interface for feature communication

**Why Services Are Mandatory:**
1. **Separation of Concerns:** Providers focus on state, services on logic
2. **Testability:** Business logic tested independently from state management
3. **Consistency:** Mirrors backend pattern (routes → services → repos)
4. **Reusability:** Other features communicate only through services
5. **Maintainability:** Changes to business logic don't affect state management

### State Management - Sealed Classes
```dart
// ✅ CORRECT - Sealed classes carry data
sealed class UserState {}
class UserLoading extends UserState {}
class UsersLoaded extends UserState {
  final List<User> users;
  UsersLoaded(this.users);
}

// ❌ WRONG - Enums can't carry data
enum UserStatus { loading, loaded }
```

**Why:** Compiler-enforced exhaustive matching + states carry data

### Riverpod Provider Lifecycle
**Problem:** Modifying provider during widget build → error

**Solution:** Delay with Future.microtask

```dart
// ✅ CORRECT
@override
void initState() {
  super.initState();
  Future.microtask(() => ref.read(provider).loadData());
}

// ❌ WRONG - modifies during build
@override
void initState() {
  super.initState();
  ref.read(provider).loadData();  // Error!
}
```

### Authorization Pattern (Client)
**Mirror server:** Permission-based checks using `PermissionChecker`

```dart
// Check permission
if (PermissionChecker.hasPermission(user, Permission.viewUsers)) {
  // Show user management screen
}

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

### Mockito Pattern (Flutter/Dart)
**Critical:** Mock parameters must be nullable to accept matchers, even when real interface has non-nullable required parameters.

```dart
// Real service interface
Future<User> createUser({
  required String name,      // Non-nullable
  required String password,  // Non-nullable
});

// Generated mock MUST use nullable parameters
Future<User> createUser({
  required String? name,     // Nullable to accept anyNamed()
  required String? password, // Nullable to accept anyNamed()
});
```

**Why:** Mockito matchers (`anyNamed()`, `any()`, `argThat()`) return `null`. Dart null safety prevents passing `null` to non-nullable parameters.

**Tests use standard matchers:**
```dart
when(mockService.createUser(
  name: anyNamed('name'),      // Returns null, needs String?
  password: anyNamed('password'),
)).thenAnswer((_) async => testUser);
```

**Reference:** See `auth_service_test.mocks.dart:42` for pattern example.

---

## Database

**Dev:** SQLite (aiosqlite)
**Prod:** PostgreSQL (asyncpg)

**Cross-Database Compatibility:**
- `UUID` TypeDecorator in `core/models.py` (PostgreSQL UUID or SQLite CHAR(36))
- `JSONList` TypeDecorator for JSON arrays (cross-DB serialization)
- Ensures consistent behavior across development and production

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

### 2025-11-19: Mockito Null Safety Pattern
- **Fixed:** Flutter test compilation errors in `user_provider_test.mocks.dart`
- **Pattern:** Mock parameters must be nullable (`String?`) to accept Mockito matchers, even when real service has non-nullable required parameters
- **Why:** Matchers (`anyNamed()`, `any()`, `argThat()`) return `null`; Dart null safety prevents passing `null` to non-nullable types
- **Solution:** Make all mock parameters nullable in `.mocks.dart` files
- **Reference:** Verified pattern in existing `auth_service_test.mocks.dart`
- **Impact:** All Flutter tests now compile correctly
- **Documentation:** Added Mockito pattern section to Testing Strategy

### 2025-11-19: User Model Migration + Core Modules
- **Completed:** Auth/Users split - User model moved from `auth/` to `users/` feature
- **Created:** `core/` directory for shared code:
  - `core/models.py` - SQLAlchemy type decorators (UUID, JSONList) for cross-DB compatibility
  - `core/enums.py` - Shared enums (UserRole) used across features
- **Added:** `name` field to User model (required field across entire stack)
- **Updated:** 26+ backend files with new import structure
- **Updated:** All Flutter user management layers (entities, DTOs, services, providers, UI)
- **Updated:** All tests (backend + Flutter) to include name field
- **Why:** Proper separation of concerns, User model belongs where CRUD operations exist
- **Pattern:** Shared types in `core/`, feature-specific models in their features
- **Tests:** 169 backend tests, 95+ Flutter tests (100% pass)

### 2025-11-19: Client User Management + Authorization
- **Added:** User CRUD in Flutter (create, edit, delete, list)
- **Added:** Client-side authorization system (permission-based, mirrors server)
- **Added:** Company dropdown for user forms (replaces manual ID entry)
- **Pattern:** Clean architecture (data → domain → presentation)
- **Pattern:** Sealed classes for state (UserState, UserLoading, UsersLoaded, etc.)
- **Pattern:** FutureProvider for reference data (companies dropdown)
- **Tests:** Added permission_checker_test, role_permissions_test, user_repository_impl_test, user_provider_test
- **Fixes:** Riverpod provider lifecycle (Future.microtask in initState)
- **Fixes:** SQLAlchemy eager loading in create/save/update (avoid lazy load errors)

### 2025-11-18: Single-Role System Migration
- **Change:** Removed dual-role (system_role + company_roles) → single `role` field
- **Why:** Simpler to understand, test, explain; reduced complexity
- **Impact:** Backend + Frontend + DB + Tests (169 passing)
- **Benefits:** 1:1 mapping (role → permission set), easier maintenance

### 2025-11-18: Security Checks (Inactive Users/Companies)
- **Added:** Login blocks inactive users/companies
- **Added:** Permission system returns empty set for inactive users/companies
- **Implementation:** Company relationship eagerly loaded for status checks
- **Tests:** Comprehensive coverage for both scenarios

### 2025-11-18: Permission-Based Authorization
- **Added:** `permission_checker.py` for centralized authorization
- **Pattern:** `require_permission(user, Permission.X)` instead of role checks
- **Benefits:** Self-documenting, testable, future-proof for dynamic roles

### 2025-11-18: Auth/Users Feature Split
- **Change:** Split `auth/` → `auth/` (authentication) + `users/` (management)
- **Why:** Align with UI (separate screens), clear responsibilities
- **Pattern:** One feature per business capability

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

**Last Updated:** 2025-11-19 (Mockito null safety pattern + User model migration + core modules)
