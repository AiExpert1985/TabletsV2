"""Tests for AuditRepository - audit log data access."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from features.audit.repository import AuditRepository
from features.audit.models import AuditLog, AuditAction


@pytest.fixture
def audit_repo(db_session):
    """Create AuditRepository with test database session."""
    return AuditRepository(db_session)


@pytest.fixture
async def sample_audit_log(db_session):
    """Create a sample audit log for testing."""
    log = AuditLog(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        user_id=uuid4(),
        username="Test User",
        user_role="company_admin",
        company_id=uuid4(),
        company_name="Test Company",
        action=AuditAction.CREATE,
        entity_type="Product",
        entity_id=str(uuid4()),
        old_values=None,
        new_values={"name": "Widget", "price": 100},
        changes=None,
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


class TestAuditRepository:
    """Test AuditRepository data access methods."""

    @pytest.mark.asyncio
    async def test_create_audit_log(self, audit_repo):
        """Create audit log succeeds."""
        # Arrange
        log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="John Doe",
            user_role="salesperson",
            company_id=uuid4(),
            company_name="ABC Corp",
            action=AuditAction.UPDATE,
            entity_type="Invoice",
            entity_id=str(uuid4()),
            old_values={"total": 100},
            new_values={"total": 120},
            changes={"total": {"old": 100, "new": 120}},
        )

        # Act
        created_log = await audit_repo.create(log)

        # Assert
        assert created_log.id is not None
        assert created_log.username == "John Doe"
        assert created_log.action == AuditAction.UPDATE
        assert created_log.entity_type == "Invoice"

    @pytest.mark.asyncio
    async def test_get_entity_history(self, audit_repo, db_session):
        """Get entity history returns all logs for that entity."""
        # Arrange
        entity_id = str(uuid4())
        company_id = uuid4()

        # Create multiple logs for same entity
        log1 = AuditLog(
            timestamp=datetime.utcnow() - timedelta(hours=2),
            user_id=uuid4(),
            username="User 1",
            user_role="company_admin",
            company_id=company_id,
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=entity_id,
            new_values={"name": "Widget"},
        )
        log2 = AuditLog(
            timestamp=datetime.utcnow() - timedelta(hours=1),
            user_id=uuid4(),
            username="User 2",
            user_role="salesperson",
            company_id=company_id,
            company_name="Test Co",
            action=AuditAction.UPDATE,
            entity_type="Product",
            entity_id=entity_id,
            old_values={"price": 100},
            new_values={"price": 120},
        )
        log3 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 3",
            user_role="accountant",
            company_id=company_id,
            company_name="Test Co",
            action=AuditAction.DELETE,
            entity_type="Product",
            entity_id=entity_id,
            old_values={"name": "Widget", "price": 120},
        )

        db_session.add_all([log1, log2, log3])
        await db_session.commit()

        # Act
        history = await audit_repo.get_entity_history("Product", entity_id)

        # Assert
        assert len(history) == 3
        # Should be ordered by timestamp descending (newest first)
        assert history[0].action == AuditAction.DELETE
        assert history[1].action == AuditAction.UPDATE
        assert history[2].action == AuditAction.CREATE

    @pytest.mark.asyncio
    async def test_get_entity_history_different_entity(self, audit_repo, sample_audit_log):
        """Get entity history for different entity returns empty."""
        # Act
        history = await audit_repo.get_entity_history("User", str(uuid4()))

        # Assert
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_logs_no_filters(self, audit_repo, db_session):
        """Get logs without filters returns all logs."""
        # Arrange
        log1 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 1",
            user_role="company_admin",
            company_id=uuid4(),
            company_name="Company A",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Product A"},
        )
        log2 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 2",
            user_role="salesperson",
            company_id=uuid4(),
            company_name="Company B",
            action=AuditAction.UPDATE,
            entity_type="Invoice",
            entity_id=str(uuid4()),
            old_values={"total": 100},
            new_values={"total": 200},
        )

        db_session.add_all([log1, log2])
        await db_session.commit()

        # Act
        logs, total = await audit_repo.get_logs()

        # Assert
        assert total >= 2  # At least our 2 logs
        assert len(logs) >= 2

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_company(self, audit_repo, db_session):
        """Get logs filtered by company ID."""
        # Arrange
        company_a = uuid4()
        company_b = uuid4()

        log1 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User A",
            user_role="company_admin",
            company_id=company_a,
            company_name="Company A",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Product A"},
        )
        log2 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User B",
            user_role="company_admin",
            company_id=company_b,
            company_name="Company B",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Product B"},
        )

        db_session.add_all([log1, log2])
        await db_session.commit()

        # Act
        logs, total = await audit_repo.get_logs(company_id=company_a)

        # Assert
        assert total >= 1
        assert all(log.company_id == company_a for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_entity_type(self, audit_repo, db_session):
        """Get logs filtered by entity type."""
        # Arrange
        log1 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 1",
            user_role="company_admin",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Widget"},
        )
        log2 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 2",
            user_role="salesperson",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Invoice",
            entity_id=str(uuid4()),
            new_values={"total": 100},
        )

        db_session.add_all([log1, log2])
        await db_session.commit()

        # Act
        logs, total = await audit_repo.get_logs(entity_type="Product")

        # Assert
        assert total >= 1
        assert all(log.entity_type == "Product" for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_action(self, audit_repo, db_session):
        """Get logs filtered by action type."""
        # Arrange
        entity_id = str(uuid4())

        log1 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 1",
            user_role="company_admin",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=entity_id,
            new_values={"name": "Widget"},
        )
        log2 = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),
            username="User 2",
            user_role="salesperson",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.UPDATE,
            entity_type="Product",
            entity_id=entity_id,
            old_values={"price": 100},
            new_values={"price": 120},
        )

        db_session.add_all([log1, log2])
        await db_session.commit()

        # Act
        logs, total = await audit_repo.get_logs(action=AuditAction.UPDATE)

        # Assert
        assert total >= 1
        assert all(log.action == AuditAction.UPDATE for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_date_range(self, audit_repo, db_session):
        """Get logs filtered by date range."""
        # Arrange
        now = datetime.utcnow()
        old_log = AuditLog(
            timestamp=now - timedelta(days=10),
            user_id=uuid4(),
            username="User 1",
            user_role="company_admin",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Old Product"},
        )
        recent_log = AuditLog(
            timestamp=now - timedelta(hours=1),
            user_id=uuid4(),
            username="User 2",
            user_role="salesperson",
            company_id=uuid4(),
            company_name="Test Co",
            action=AuditAction.CREATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            new_values={"name": "Recent Product"},
        )

        db_session.add_all([old_log, recent_log])
        await db_session.commit()

        # Act
        start_date = now - timedelta(days=2)
        logs, total = await audit_repo.get_logs(start_date=start_date)

        # Assert
        assert total >= 1
        assert all(log.timestamp >= start_date for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_pagination(self, audit_repo, db_session):
        """Get logs with pagination works correctly."""
        # Arrange - Create multiple logs
        for i in range(5):
            log = AuditLog(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                user_id=uuid4(),
                username=f"User {i}",
                user_role="company_admin",
                company_id=uuid4(),
                company_name="Test Co",
                action=AuditAction.CREATE,
                entity_type="Product",
                entity_id=str(uuid4()),
                new_values={"name": f"Product {i}"},
            )
            db_session.add(log)
        await db_session.commit()

        # Act
        logs_page1, total = await audit_repo.get_logs(limit=2, offset=0)
        logs_page2, _ = await audit_repo.get_logs(limit=2, offset=2)

        # Assert
        assert total >= 5
        assert len(logs_page1) == 2
        assert len(logs_page2) == 2
        # Pages should have different logs
        assert logs_page1[0].id != logs_page2[0].id

    @pytest.mark.asyncio
    async def test_get_logs_multiple_filters(self, audit_repo, db_session):
        """Get logs with multiple filters combines them correctly."""
        # Arrange
        company_id = uuid4()
        user_id = uuid4()

        matching_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username="Target User",
            user_role="company_admin",
            company_id=company_id,
            company_name="Target Company",
            action=AuditAction.UPDATE,
            entity_type="Product",
            entity_id=str(uuid4()),
            old_values={"price": 100},
            new_values={"price": 120},
        )
        non_matching_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=uuid4(),  # Different user
            username="Other User",
            user_role="salesperson",
            company_id=company_id,  # Same company
            company_name="Target Company",
            action=AuditAction.CREATE,
            entity_type="Invoice",
            entity_id=str(uuid4()),
            new_values={"total": 100},
        )

        db_session.add_all([matching_log, non_matching_log])
        await db_session.commit()

        # Act - Filter by company, user, and action
        logs, total = await audit_repo.get_logs(
            company_id=company_id,
            user_id=user_id,
            action=AuditAction.UPDATE,
        )

        # Assert
        assert total >= 1
        assert all(
            log.company_id == company_id
            and log.user_id == user_id
            and log.action == AuditAction.UPDATE
            for log in logs
        )
