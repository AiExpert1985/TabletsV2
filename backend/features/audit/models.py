"""Audit trail models for tracking entity changes."""

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, Index, TypeDecorator
from sqlalchemy.dialects.postgresql import JSON as PG_JSON

from core.database import Base
from features.auth.models import UUID


class JSON(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's JSON type when available, otherwise uses TEXT for SQLite.
    Stores JSON objects/dicts as strings.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # PostgreSQL handles JSON natively
        else:
            # For SQLite: store as JSON string
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            # For SQLite: parse JSON string
            try:
                return json.loads(value) if value else None
            except (json.JSONDecodeError, TypeError):
                return None


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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Actor (Who)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    username = Column(String(255), nullable=False)  # Cached - user might be deleted
    user_role = Column(String(50), nullable=False)  # Role at time of action

    # Multi-tenancy (Where)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Null for system admin actions
    company_name = Column(String(255), nullable=True)  # Cached for display

    # Operation (What)
    action = Column(String(10), nullable=False)  # CREATE, UPDATE, DELETE
    entity_type = Column(String(50), nullable=False, index=True)  # User, Product, Invoice
    entity_id = Column(String(36), nullable=False, index=True)  # UUID as string

    # Details (Changes)
    old_values = Column(JSON(), nullable=True)  # Before state (null for CREATE)
    new_values = Column(JSON(), nullable=True)  # After state (null for DELETE)
    changes = Column(JSON(), nullable=True)  # Computed delta for UPDATE

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
