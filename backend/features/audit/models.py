"""Audit trail models for tracking entity changes."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from core.database.base import Base
from core.database.guid import GUID


class AuditAction:
    """Audit action constants."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(Base):
    """
    Audit log for tracking all entity changes.

    Tracks WHO did WHAT to WHICH entity and WHEN, with full change details.
    """
    __tablename__ = "audit_logs"

    # Identity
    id = Column(GUID, primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Actor (Who)
    user_id = Column(GUID, nullable=False, index=True)
    username = Column(String(255), nullable=False)  # Cached - user might be deleted
    user_role = Column(String(50), nullable=False)  # Role at time of action

    # Multi-tenancy (Where)
    company_id = Column(GUID, nullable=True, index=True)  # Null for system admin actions
    company_name = Column(String(255), nullable=True)  # Cached for display

    # Operation (What)
    action = Column(String(10), nullable=False)  # CREATE, UPDATE, DELETE
    entity_type = Column(String(50), nullable=False, index=True)  # User, Product, Invoice
    entity_id = Column(String(36), nullable=False, index=True)  # UUID as string

    # Details (Changes)
    old_values = Column(JSONB, nullable=True)  # Before state (null for CREATE)
    new_values = Column(JSONB, nullable=True)  # After state (null for DELETE)
    changes = Column(JSONB, nullable=True)  # Computed delta for UPDATE

    # Optional description
    description = Column(Text, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_logs_company_timestamp', 'company_id', 'timestamp'),
        Index('ix_audit_logs_entity', 'entity_type', 'entity_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"entity_type={self.entity_type}, user={self.username})>"
        )
