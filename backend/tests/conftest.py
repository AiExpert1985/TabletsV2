"""Pytest configuration and fixtures for backend tests."""
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from core.database import Base
from core.config import Settings, get_settings
from core.security import hash_password

# Import all models so SQLAlchemy can map relationships
from features.auth.models import User, UserRole, RefreshToken
from features.company.models import Company
from features.product.models import Product

# Import repositories and services
from features.users.repository import UserRepository
from features.auth.repository import RefreshTokenRepository
from features.auth.auth_services import AuthService
from features.company.repository import CompanyRepository


# ============================================================================
# Test Settings
# ============================================================================

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        APP_NAME="TabletsV2 Test",
        DEBUG=True,
        # File-based test DB with transaction rollback for isolation
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        JWT_SECRET_KEY="test-secret-key-for-testing-only-not-for-production",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        REFRESH_TOKEN_EXPIRE_DAYS=30,
        BCRYPT_ROUNDS=4,  # Faster for tests
        PASSWORD_MIN_LENGTH=8,
        LOGIN_RATE_LIMIT_ATTEMPTS=5,
        LOGIN_RATE_LIMIT_WINDOW_MINUTES=60,
        DEFAULT_COUNTRY_CODE="+964",
    )


@pytest.fixture(scope="session", autouse=True)
def override_settings(test_settings: Settings):
    """Override settings globally for all tests."""
    get_settings.cache_clear()

    # Monkey-patch the settings
    import core.config
    original_get_settings = core.config.get_settings
    core.config.get_settings = lambda: test_settings

    yield

    # Restore original
    core.config.get_settings = original_get_settings


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # No connection pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create fresh database session for each test with transaction rollback."""
    # Start a connection
    async with test_engine.connect() as connection:
        # Begin a transaction
        trans = await connection.begin()

        # Create session bound to the transaction
        async_session = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session() as session:
            yield session

            # Rollback transaction to clean up test data
            await trans.rollback()


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create user repository."""
    return UserRepository(db_session)


@pytest.fixture
def refresh_token_repo(db_session: AsyncSession) -> RefreshTokenRepository:
    """Create refresh token repository."""
    return RefreshTokenRepository(db_session)


@pytest.fixture
def company_repo(db_session: AsyncSession) -> CompanyRepository:
    """Create company repository."""
    return CompanyRepository(db_session)


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def auth_service(user_repo: UserRepository, refresh_token_repo: RefreshTokenRepository) -> AuthService:
    """Create auth service."""
    return AuthService(user_repo=user_repo, refresh_token_repo=refresh_token_repo)


# ============================================================================
# Data Fixtures - Company
# ============================================================================

@pytest.fixture
async def test_company(company_repo: CompanyRepository) -> Company:
    """Create test company."""
    company = await company_repo.create(name="Test Company")
    return company


# ============================================================================
# Data Fixtures - Users
# ============================================================================

@pytest.fixture
async def test_user(user_repo: UserRepository, test_company: Company) -> User:
    """Create regular test user with viewer role."""
    user = await user_repo.create(
        phone_number="9647700000001",
        hashed_password=hash_password("TestPassword123"),
        company_id=str(test_company.id),
        role="viewer",
    )
    return user


@pytest.fixture
async def test_admin_user(user_repo: UserRepository, test_company: Company) -> User:
    """Create admin test user."""
    user = await user_repo.create(
        phone_number="9647700000002",
        hashed_password=hash_password("AdminPassword123"),
        company_id=str(test_company.id),
        role="company_admin",
    )
    return user


@pytest.fixture
async def test_system_admin(user_repo: UserRepository) -> User:
    """Create system admin test user."""
    user = await user_repo.create(
        phone_number="9647700000000",
        hashed_password=hash_password("SystemAdminPassword123"),
        company_id=None,
        role="system_admin",
    )
    return user


# ============================================================================
# Test Credentials
# ============================================================================

@pytest.fixture
def valid_phone() -> str:
    """Valid phone number for tests."""
    return "9647700000001"


@pytest.fixture
def valid_password() -> str:
    """Valid password for tests."""
    return "TestPassword123"


@pytest.fixture
def invalid_password() -> str:
    """Invalid password for tests."""
    return "WrongPassword123"
