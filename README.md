# TabletsV2 ERP - Authentication System

Complete authentication system for TabletsV2 ERP using FastAPI (backend) and Flutter (client).

## Architecture Overview

**Backend:** FastAPI + SQLAlchemy (async) + PostgreSQL
**Client:** Flutter + Riverpod + Go Router + Dio

### Key Design Decisions

- **Phone-first authentication** - Iraqi mobile numbers (+964)
- **Single refresh token per user** - New login invalidates old tokens (single device)
- **JWT tokens** - Stateless access tokens, refresh tokens stored (hashed) in DB
- **Repository pattern** - Data access abstraction for testability
- **Clean architecture** - Simplified for Phase 1 (no use cases, ORM models directly)

---

## Project Structure

```
TabletsV2/
├── backend/                 # FastAPI server
│   ├── core/               # Core utilities
│   │   ├── config.py       # Environment configuration
│   │   ├── database.py     # SQLAlchemy setup
│   │   ├── security.py     # JWT, bcrypt, phone validation, rate limiting
│   │   ├── exceptions.py   # Custom exceptions
│   │   └── dependencies.py # FastAPI dependencies
│   ├── features/
│   │   └── auth/           # Auth feature
│   │       ├── models.py           # ORM models (User, RefreshToken, PasswordResetToken)
│   │       ├── repository.py       # Data access layer
│   │       ├── services.py         # Business logic
│   │       ├── schemas.py          # Pydantic DTOs
│   │       ├── routes.py           # FastAPI endpoints
│   │       ├── dependencies.py     # Auth dependencies
│   │       └── notifications.py    # Email/SMS abstraction (unimplemented)
│   ├── main.py             # FastAPI app
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
│
└── client/                 # Flutter app
    ├── lib/
    │   ├── core/
    │   │   ├── config/             # App configuration
    │   │   ├── network/            # HTTP client abstraction
    │   │   │   ├── http_client.dart        # Abstract interface
    │   │   │   ├── http_exception.dart
    │   │   │   ├── interceptors/           # Auth & logging interceptors
    │   │   │   └── impl/
    │   │   │       └── dio_http_client.dart # Dio implementation
    │   │   ├── storage/            # Token storage (FlutterSecureStorage)
    │   │   ├── router/             # Go Router configuration
    │   │   └── utils/              # Validators (phone, password)
    │   ├── features/
    │   │   └── auth/
    │   │       ├── domain/         # Entities & repository interfaces
    │   │       ├── data/           # Models, datasources, repository impl
    │   │       └── presentation/   # Providers (Riverpod) & screens (UI)
    │   └── main.dart
    └── pubspec.yaml
```

---

## Backend Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Virtual environment (recommended)

### Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   ```bash
   # Create database
   psql -U postgres
   CREATE DATABASE tabletsv2;
   \q
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:
   ```env
   DATABASE_URL="postgresql+asyncpg://postgres:your_password@localhost:5432/tabletsv2"
   JWT_SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
   DEBUG=True
   ```

6. **Initialize database (creates tables):**
   ```bash
   python -c "import asyncio; from main import app; from core.database import init_db; asyncio.run(init_db())"
   ```

   Or run the server once (it will auto-create tables):
   ```bash
   python main.py
   ```

### Running the Server

```bash
python main.py
```

Server will start at: `http://localhost:8000`

API docs available at: `http://localhost:8000/docs`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/signup` | Register new user |
| `POST` | `/auth/login` | Login with phone + password |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | Logout (revoke refresh token) |
| `GET`  | `/auth/me` | Get current user (requires auth) |
| `POST` | `/auth/password/request-reset` | Request password reset |
| `POST` | `/auth/password/reset` | Reset password with token |
| `POST` | `/auth/password/change` | Change password (requires auth) |

---

## Client Setup

### Prerequisites

- Flutter 3.7.0+
- Dart 3.7.0+

### Installation

1. **Navigate to client directory:**
   ```bash
   cd client
   ```

2. **Install dependencies:**
   ```bash
   flutter pub get
   ```

3. **Update API URL (for local development):**

   Edit `lib/core/config/app_config.dart`:
   ```dart
   static const String baseUrl = 'http://localhost:8000';  // Default
   // For Android emulator: 'http://10.0.2.2:8000'
   // For iOS simulator: 'http://localhost:8000'
   // For physical device: 'http://YOUR_LOCAL_IP:8000'
   ```

### Running the App

```bash
flutter run
```

**Note:** If running on Android emulator and connecting to local backend:
- Use `http://10.0.2.2:8000` as base URL (Android emulator's alias for host machine)

**Note:** If running on physical device:
- Ensure device and server are on same network
- Use your machine's local IP: `http://192.168.x.x:8000`

---

## Features Implemented

### ✅ Phase 1 Complete

**Backend:**
- User signup (phone + password)
- Login with phone + password
- JWT access token (30 min expiry)
- JWT refresh token (30 day expiry, single-use)
- Token refresh endpoint
- Logout (revoke refresh token)
- Get current user
- Password reset flow (token-based, 15 min expiry)
- Change password (authenticated)
- Phone number normalization (E.164 format)
- Password validation (min 8 chars, uppercase, lowercase, digit)
- Bcrypt password hashing (cost 12)
- Rate limiting (5 login attempts per phone per hour)
- HMAC-SHA256 token hashing for storage

**Client:**
- Signup screen
- Login screen
- Auto token refresh
- Logout
- Phone number validation
- Password strength validation
- Secure token storage (FlutterSecureStorage)
- HTTP client abstraction (Dio implementation)
- Auth interceptor (auto-add Bearer token)
- Go Router with auth guards

### Security Features

1. **Token Security:**
   - Refresh tokens hashed with HMAC-SHA256 before storage
   - One-time use refresh tokens (revoked after refresh)
   - Single refresh token per user (new login invalidates old)

2. **Password Security:**
   - Bcrypt hashing (cost 12)
   - Strength validation (uppercase, lowercase, digit, min 8 chars)

3. **Rate Limiting:**
   - In-memory rate limiter (Phase 1)
   - 5 failed login attempts per phone per hour
   - Reset counter on successful login

4. **Phone Validation:**
   - Iraqi mobile format: `^(?:\+964|964|0)?7[3-9]\d{8}$`
   - Normalized to E.164: `+9647501234567`

5. **API Security:**
   - CORS enabled (configure in production)
   - JWT Bearer authentication
   - Account deactivation support

---

## Testing

### Backend

1. **Test signup:**
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "07501234567", "password": "Test1234", "password_confirm": "Test1234"}'
   ```

2. **Test login:**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "07501234567", "password": "Test1234"}'
   ```

3. **Test get current user:**
   ```bash
   curl -X GET http://localhost:8000/auth/me \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Client

1. Run app: `flutter run`
2. Navigate to signup screen
3. Enter phone: `07501234567`
4. Enter password: `Test1234`
5. Confirm password: `Test1234`
6. Click "Sign Up"
7. Should redirect to home screen

---

## Troubleshooting

### Backend

**Database connection error:**
```
Check DATABASE_URL in .env
Ensure PostgreSQL is running: sudo systemctl status postgresql
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**JWT secret key error:**
```bash
# Generate a secure key
openssl rand -hex 32
# Add to .env as JWT_SECRET_KEY
```

### Client

**Build errors after pub get:**
```bash
flutter clean
flutter pub get
flutter run
```

**Cannot connect to backend:**
- Check base URL in `app_config.dart`
- For Android emulator: use `http://10.0.2.2:8000`
- For physical device: use local IP `http://192.168.x.x:8000`
- Ensure backend is running: `curl http://localhost:8000/health`

**FlutterSecureStorage errors on Android:**
- Min SDK must be 18+ (check `android/app/build.gradle`)

---

## Phase 2 (Future Enhancements)

### Planned Features:
- ✉️ Email/SMS integration for password reset
- 📱 OTP verification on signup
- 🔐 Email login support
- 🌐 Social auth (Google, Apple)
- 🔒 Two-factor authentication (2FA)
- 👆 Biometric login (Face ID, fingerprint)
- 📊 Advanced rate limiting (Redis)
- 💾 Session management UI ("logout other devices")
- 🗑️ Account deletion
- 📧 Email verification

---

## Database Schema

### `users` table
```sql
id                 UUID PRIMARY KEY
phone_number       VARCHAR(20) UNIQUE NOT NULL
email              VARCHAR(255) UNIQUE NULL
hashed_password    VARCHAR(255) NOT NULL
is_active          BOOLEAN DEFAULT TRUE
is_phone_verified  BOOLEAN DEFAULT FALSE
created_at         TIMESTAMP
updated_at         TIMESTAMP
last_login_at      TIMESTAMP NULL
```

### `refresh_tokens` table
```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id) ON DELETE CASCADE
token_id        VARCHAR(255) UNIQUE NOT NULL
token_hash      VARCHAR(255) UNIQUE NOT NULL
expires_at      TIMESTAMP NOT NULL
created_at      TIMESTAMP
revoked_at      TIMESTAMP NULL
device_info     VARCHAR NULL
```

### `password_reset_tokens` table
```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id) ON DELETE CASCADE
token_hash      VARCHAR(255) UNIQUE NOT NULL
expires_at      TIMESTAMP NOT NULL
created_at      TIMESTAMP
used_at         TIMESTAMP NULL
```

---

## Contributing

### Code Style
- **Backend:** PEP 8, type hints, docstrings
- **Client:** Dart style guide, effective Dart

### Architecture Guidelines
- Keep functions small (20-30 lines)
- Single responsibility per function/class
- Use early returns (avoid deep nesting)
- Inject dependencies, don't hard-code
- Abstract only when needed (3+ implementations or external services)

---

## License

MIT License

---

## Contact

For questions or issues, please open a GitHub issue.
