"""Tests for Audit Routes - HTTP API endpoints."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient

from features.audit.models import AuditLog, AuditAction
from features.auth.models import User, UserRole, RefreshToken
from features.company.models import Company
from core.security import hash_password, create_access_token


@pytest.fixture
async def test_company(db_session):
    """Create test company."""
    company = Company(
        id=uuid4(),
        name="Test Company",
        is_active=True,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def system_admin_user(db_session):
    """Create system admin user."""
    user = User(
        id=uuid4(),
        phone_number="07700000001",
        hashed_password=hash_password("AdminPass123"),
        name="System Admin",
        role=UserRole.SYSTEM_ADMIN,
        company_id=None,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def company_admin_user(db_session, test_company):
    """Create company admin user."""
    user = User(
        id=uuid4(),
        phone_number="07700000002",
        hashed_password=hash_password("CompanyAdmin123"),
        name="Company Admin",
        role=UserRole.COMPANY_ADMIN,
        company_id=test_company.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ["company"])
    return user


@pytest.fixture
async def regular_user(db_session, test_company):
    """Create regular user (salesperson)."""
    user = User(
        id=uuid4(),
        phone_number="07700000003",
        hashed_password=hash_password("UserPass123"),
        name="Regular User",
        role=UserRole.SALESPERSON,
        company_id=test_company.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def system_admin_token(system_admin_user):
    """Create access token for system admin."""
    return create_access_token(system_admin_user.id)


@pytest.fixture
def company_admin_token(company_admin_user):
    """Create access token for company admin."""
    return create_access_token(company_admin_user.id)


@pytest.fixture
def regular_user_token(regular_user):
    """Create access token for regular user."""
    return create_access_token(regular_user.id)


@pytest.fixture
async def sample_audit_logs(db_session, test_company, company_admin_user):
    """Create sample audit logs."""
    logs = []

    # Log 1: Product creation
    log1 = AuditLog(
        timestamp=datetime.utcnow() - timedelta(hours=3),
        user_id=company_admin_user.id,
        username=company_admin_user.name,
        user_role=company_admin_user.role,
        company_id=test_company.id,
        company_name=test_company.name,
        action=AuditAction.CREATE,
        entity_type="Product",
        entity_id=str(uuid4()),
        new_values={"name": "Widget A", "price": 100},
    )
    logs.append(log1)

    # Log 2: Product update
    log2 = AuditLog(
        timestamp=datetime.utcnow() - timedelta(hours=2),
        user_id=company_admin_user.id,
        username=company_admin_user.name,
        user_role=company_admin_user.role,
        company_id=test_company.id,
        company_name=test_company.name,
        action=AuditAction.UPDATE,
        entity_type="Product",
        entity_id=log1.entity_id,  # Same product
        old_values={"price": 100},
        new_values={"price": 120},
        changes={"price": {"old": 100, "new": 120}},
    )
    logs.append(log2)

    # Log 3: User creation
    log3 = AuditLog(
        timestamp=datetime.utcnow() - timedelta(hours=1),
        user_id=company_admin_user.id,
        username=company_admin_user.name,
        user_role=company_admin_user.role,
        company_id=test_company.id,
        company_name=test_company.name,
        action=AuditAction.CREATE,
        entity_type="User",
        entity_id=str(uuid4()),
        new_values={"name": "New User", "role": "salesperson"},
    )
    logs.append(log3)

    db_session.add_all(logs)
    await db_session.commit()

    return logs


class TestAuditRoutes:
    """Test Audit HTTP API endpoints."""

    # ========================================================================
    # GET /api/audit-logs - Global Audit Log Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_audit_logs_system_admin_success(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """System admin can get all audit logs."""
        # Act
        response = await async_client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_get_audit_logs_company_admin_success(
        self, async_client: AsyncClient, company_admin_token, sample_audit_logs
    ):
        """Company admin can get their company's audit logs."""
        # Act
        response = await async_client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {company_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        # All logs should be from their company
        assert all(
            log["company_id"] == str(sample_audit_logs[0].company_id)
            for log in data["items"]
            if log["company_id"] is not None
        )

    @pytest.mark.asyncio
    async def test_get_audit_logs_regular_user_forbidden(
        self, async_client: AsyncClient, regular_user_token
    ):
        """Regular user cannot access audit logs."""
        # Act
        response = await async_client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_audit_logs_unauthorized(self, async_client: AsyncClient):
        """Unauthorized request returns 401."""
        # Act
        response = await async_client.get("/api/audit-logs")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_entity_type(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Filter audit logs by entity type."""
        # Act
        response = await async_client.get(
            "/api/audit-logs?entity_type=Product",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["entity_type"] == "Product" for log in data["items"])

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_action(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Filter audit logs by action."""
        # Act
        response = await async_client.get(
            "/api/audit-logs?action=UPDATE",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(log["action"] == "UPDATE" for log in data["items"])

    @pytest.mark.asyncio
    async def test_get_audit_logs_pagination(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Pagination works correctly."""
        # Act
        response = await async_client.get(
            "/api/audit-logs?limit=2&offset=0",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_date_range(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Filter audit logs by date range."""
        # Arrange
        start_date = (datetime.utcnow() - timedelta(hours=2.5)).isoformat()

        # Act
        response = await async_client.get(
            f"/api/audit-logs?start_date={start_date}",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should get logs from last 2.5 hours
        assert len(data["items"]) >= 2

    @pytest.mark.asyncio
    async def test_get_audit_logs_company_admin_cannot_see_other_companies(
        self, async_client: AsyncClient, company_admin_token, db_session
    ):
        """Company admin cannot see other companies' logs."""
        # Arrange - Create log for different company
        other_company = Company(id=uuid4(), name="Other Company", is_active=True)
        db_session.add(other_company)

        other_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="Other User",
            user_role=UserRole.COMPANY_ADMIN,
            company_id=other_company.id,
            company_name=other_company.name,
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Other Product"},
        )
        db_session.add(other_log)
        await db_session.commit()

        # Act
        response = await async_client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {company_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should not see the other company's log
        assert not any(
            log["company_id"] == str(other_company.id)
            for log in data["items"]
        )

    # ========================================================================
    # GET /api/audit-logs/{entity_type}/{entity_id} - Entity History Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_entity_history_success(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Get entity history returns all logs for that entity."""
        # Arrange
        product_id = sample_audit_logs[0].entity_id

        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{product_id}",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "Product"
        assert data["entity_id"] == product_id
        assert len(data["history"]) == 2  # CREATE and UPDATE

    @pytest.mark.asyncio
    async def test_get_entity_history_empty(
        self, async_client: AsyncClient, system_admin_token
    ):
        """Get entity history for non-existent entity returns empty."""
        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{uuid4()}",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 0

    @pytest.mark.asyncio
    async def test_get_entity_history_company_user_filtered(
        self, async_client: AsyncClient, company_admin_token, sample_audit_logs, db_session
    ):
        """Company user only sees their company's entity history."""
        # Arrange - Create log for same entity but different company
        other_company = Company(id=uuid4(), name="Other Company", is_active=True)
        db_session.add(other_company)

        product_id = sample_audit_logs[0].entity_id
        other_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="Other User",
            user_role=UserRole.COMPANY_ADMIN,
            company_id=other_company.id,
            company_name=other_company.name,
            action=AuditAction.DELETE,
            entity_type="Product",
            entity_id=product_id,  # Same product ID
            old_values={"name": "Widget"},
        )
        db_session.add(other_log)
        await db_session.commit()

        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{product_id}",
            headers={"Authorization": f"Bearer {company_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only see their company's logs (CREATE and UPDATE, not DELETE)
        assert len(data["history"]) == 2
        assert all(
            log["company_id"] != str(other_company.id)
            for log in data["history"]
        )

    @pytest.mark.asyncio
    async def test_get_entity_history_regular_user_success(
        self, async_client: AsyncClient, regular_user_token, sample_audit_logs
    ):
        """Regular user can access entity history (for History button)."""
        # Arrange
        product_id = sample_audit_logs[0].entity_id

        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{product_id}",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2

    @pytest.mark.asyncio
    async def test_get_entity_history_unauthorized(self, async_client: AsyncClient):
        """Unauthorized request returns 401."""
        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{uuid4()}"
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_entity_history_ordered_by_timestamp(
        self, async_client: AsyncClient, system_admin_token, sample_audit_logs
    ):
        """Entity history is ordered by timestamp descending (newest first)."""
        # Arrange
        product_id = sample_audit_logs[0].entity_id

        # Act
        response = await async_client.get(
            f"/api/audit-logs/Product/{product_id}",
            headers={"Authorization": f"Bearer {system_admin_token}"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        history = data["history"]

        # First should be UPDATE (newer), second should be CREATE (older)
        assert history[0]["action"] == "UPDATE"
        assert history[1]["action"] == "CREATE"
