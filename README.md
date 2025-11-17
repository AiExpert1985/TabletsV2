# TabletsV2 ERP

Multi-tenant ERP system with FastAPI backend and Flutter client.

**Tech Stack:**
- **Backend:** FastAPI + SQLAlchemy (async) + PostgreSQL/SQLite
- **Client:** Flutter + Riverpod + Go Router + Dio

> **📚 Understanding the Project**
> For architectural decisions, patterns, and design rationale, see [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md).
> For AI assistant guidelines, see [`docs/AI_GUIDELINES.md`](docs/AI_GUIDELINES.md).

---

## Project Structure

```
TabletsV2/
├── backend/                 # FastAPI server
│   ├── core/               # Config, database, security, exceptions
│   ├── features/           # Feature modules (auth, products, etc.)
│   │   └── [feature]/      # Each feature has: models, repository, services, routes, schemas
│   ├── scripts/            # Database & admin scripts
│   ├── tests/              # Backend tests
│   ├── main.py             # FastAPI application entry point
│   └── pyproject.toml      # Python dependencies
│
├── client/                 # Flutter app
│   ├── lib/
│   │   ├── core/           # Config, network, storage, router, utils
│   │   ├── features/       # Feature modules
│   │   │   └── [feature]/  # Each feature has: domain, data, presentation
│   │   └── main.dart
│   ├── test/               # Client tests
│   └── pubspec.yaml        # Flutter dependencies
│
└── docs/                   # Documentation
    ├── PROJECT_CONTEXT.md  # Architecture, decisions, patterns
    └── AI_GUIDELINES.md    # AI assistant guidelines
```

---

## Backend Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (production) or SQLite (development)

### Quick Start

1. **Navigate and setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set DATABASE_URL, JWT_SECRET_KEY
   # Generate secret: openssl rand -hex 32
   ```

3. **Initialize database:**
   ```bash
   # Quick reset with seed data
   python scripts/db/reset_database.py

   # Default login after reset:
   # System Admin: 07700000000 / Admin123
   # Company Admin: 07701111111 / Admin123
   ```

4. **Run server:**
   ```bash
   python main.py
   ```
   - Server: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

### Running Tests

```bash
cd backend
pytest                    # All tests
pytest tests/test_auth.py # Specific module
```

---

## Client Setup

### Prerequisites
- Flutter 3.7.0+
- Dart 3.7.0+

### Quick Start

1. **Navigate and setup:**
   ```bash
   cd client
   flutter pub get
   ```

2. **Configure API URL** (edit `lib/core/config/app_config.dart`):
   ```dart
   static const String baseUrl = 'http://localhost:8000';      // Default
   // Android emulator: 'http://10.0.2.2:8000'
   // Physical device: 'http://YOUR_LOCAL_IP:8000'
   ```

3. **Run app:**
   ```bash
   flutter run
   ```

### Running Tests

```bash
cd client
flutter test                      # All tests
flutter test test/core/utils/     # Specific folder
```

---

## Current Features

**Core:**
- Multi-tenant architecture with company isolation
- Phone-first authentication (Iraqi +964 numbers)
- Role-based permissions (36 granular permissions)
- Products module (basic CRUD)

**Security:**
- JWT tokens with refresh flow
- Bcrypt password hashing (cost 12)
- Rate limiting (5 attempts/phone/hour)
- Single refresh token per user

> **📋 Complete Feature List**
> See [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) for detailed feature status, security implementation, and deferred features.

---

## Troubleshooting

### Backend Issues

**Database connection error:**
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`

**Import errors:**
```bash
source venv/bin/activate  # Ensure virtual environment is activated
```

**JWT errors:**
```bash
openssl rand -hex 32  # Generate secret, add to .env as JWT_SECRET_KEY
```

### Client Issues

**Cannot connect to backend:**
- Check `baseUrl` in `lib/core/config/app_config.dart`
- Android emulator: use `http://10.0.2.2:8000`
- Physical device: use local IP `http://192.168.x.x:8000`
- Verify backend is running: `curl http://localhost:8000/docs`

**Build errors:**
```bash
flutter clean && flutter pub get && flutter run
```

---

## Useful Scripts

**Database:**
- `backend/scripts/db/reset_database.py` - Drop/recreate/seed database
- `backend/scripts/admin/create_system_admin.py` - Create system admin (CLI only)

**Testing:**
- `pytest` (backend), `flutter test` (client)

---

## License

MIT License
