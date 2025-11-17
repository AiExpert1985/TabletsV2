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

### 3. Repository Pattern
**Decision:** ABC (Abstract Base Classes) instead of Protocol
**Rationale:** Better clarity, IDE support, runtime enforcement
**Previous:** Used Protocol (structural typing)

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

### 1. Multi-Tenancy Isolation
- Never bypass `CompanyContext` filtering
- System admin queries must explicitly handle `company_id = NULL`
- Always use `BaseRepository` for company-scoped entities

### 2. Security
- No public signup - admin creation CLI-only
- Single refresh token per user (logout other devices)
- Phone numbers are unique identifiers (not usernames)
- Bcrypt rounds = 12 (don't lower for "performance")

### 3. Type Safety
- Backend: Always use type hints
- Client: Always use sealed classes for state (not enums)
- Never use `dynamic` or `Any` unless absolutely necessary

### 4. Testing
- Don't chase 100% coverage
- Focus on service layer and critical business logic
- Skip framework internals and UI widgets (use integration tests)

### 5. Architecture
- Maintain 3-layer separation (don't merge repositories into services)
- Keep feature-based structure (user, product, company)
- Service layer = business logic only (no state management)

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

## Recent Changes & Sessions

### Session: Initial Setup
- Created 3-layer clean architecture
- Implemented multi-tenancy with company isolation
- Set up phone-first authentication
- Created 95+ client tests + 86+ backend tests

### Session: Project Reorganization
- Moved documentation to `docs/` folder
- Consolidated scripts into `backend/scripts/db/` and `backend/scripts/admin/`
- Removed redundant `CODING_GUIDELINES.md` (replaced by AI_GUIDELINES.md + PROJECT_CONTEXT.md)
- Migrated dependencies to `pyproject.toml`
- Created this PROJECT_CONTEXT.md file for AI assistant handoffs

---

**Last Updated:** 2025-11-17
**Active Branch:** `claude/review-project-structure-01G2F5HffWoiF8XAJkdcxiRS`
