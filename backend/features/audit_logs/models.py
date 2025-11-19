"""SQLAlchemy ORM models for audit logging."""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from core.models import UUID
from core.enums import AuditAction, EntityType

if TYPE_CHECKING:
    from features.users.models import User


class AuditLog(Base):
    """
    Audit log for tracking changes to business entities.

    Tracks CREATE, UPDATE, DELETE operations on User, Company, Product entities.
    Multi-tenancy: system_admin sees all, company_admin sees their company.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # What was changed
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, native_enum=False, length=50),
        nullable=False,
        index=True
    )
    entity_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, native_enum=False, length=50),
        nullable=False,
        index=True
    )

    # Change details (JSON: {field: {old: val, new: val}} for UPDATE, {field: val} for CREATE/DELETE)
    changes: Mapped[str] = mapped_column(Text, nullable=False)

    # Who made the change
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # NULL if user deleted
        index=True
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Multi-tenancy: NULL for system_admin actions, company_id for company user actions
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id]
    )

    def __repr__(self):
        return f"<AuditLog {self.action.value} {self.entity_type.value} by {self.username}>"
