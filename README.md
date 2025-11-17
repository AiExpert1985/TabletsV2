# TabletsV2 ERP

Multi-tenant ERP system with FastAPI backend and Flutter client.

**Tech Stack:** FastAPI + SQLAlchemy (async) + Flutter + Riverpod

> **📚 Documentation:** [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) | [`docs/AI_GUIDELINES.md`](docs/AI_GUIDELINES.md)

---

## Backend Setup

### Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

### Environment Setup

Create `.env` file:
```env
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
DATABASE_URL=sqlite+aiosqlite:///./dev.db
DEBUG=True
```

### Database Initialization

**Option 1: Complete Setup (Recommended)**
```bash
python scripts/db/setup_all.py
```
Creates database, admin (07701791983 / Admin789), and sample data.

**Option 2: Step by Step**
```bash
python scripts/db/reset_db.py       # Reset database
python scripts/db/create_admin.py   # Create admin (07701791983 / Admin789)
python scripts/db/seed_data.py      # Populate with sample data
```

### Run Server

```bash
python main.py
```
- Server: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Run Tests

```bash
pytest                    # All tests
pytest tests/test_auth.py # Specific module
```

---

## Client Setup

### Quick Start

```bash
cd client
flutter pub get
flutter run
```

### Configure API

Edit `lib/core/config/app_config.dart`:
```dart
static const String baseUrl = 'http://localhost:8000';      // Default
// Android emulator: 'http://10.0.2.2:8000'
// Physical device: 'http://YOUR_LOCAL_IP:8000'
```

### Run Tests

```bash
flutter test
```

---

## Features

- Multi-tenant with company isolation
- Phone-first auth (Iraqi +964 numbers)
- JWT with refresh tokens
- Role-based permissions (36 granular)
- Products module (CRUD)

> See [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) for complete feature list and architecture.

---

## Troubleshooting

**Backend connection issues:**
- Check `.env` file exists with `JWT_SECRET_KEY` and `DATABASE_URL`
- Verify virtual environment: `source venv/bin/activate`

**Client connection issues:**
- Android emulator: use `http://10.0.2.2:8000`
- Physical device: use local IP `http://192.168.x.x:8000`
- Verify backend is running: `curl http://localhost:8000/docs`

**Build errors:**
```bash
flutter clean && flutter pub get && flutter run
```

---

## Scripts Reference

All scripts in `backend/scripts/db/`:

| Script | Purpose |
|--------|---------|
| `setup_all.py` | Complete setup: reset + admin + seed data |
| `reset_db.py` | Drop and recreate database tables |
| `create_admin.py` | Create system admin (07701791983 / Admin789) |
| `seed_data.py` | Populate database from seed_data.json |

---

## License

MIT License
