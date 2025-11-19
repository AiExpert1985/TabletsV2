"""Shared SQLAlchemy type decorators for cross-database compatibility."""
import uuid
import json
from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON as PG_JSON


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36) for SQLite.
    Stores UUID as string with hyphens for consistency.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            # For SQLite: store as string with hyphens
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        # Convert string back to UUID
        return uuid.UUID(value)


class JSONList(TypeDecorator):
    """Platform-independent JSON list type.

    Uses PostgreSQL's JSON type when available, otherwise uses TEXT for SQLite.
    Stores lists as JSON strings.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value  # PostgreSQL handles JSON natively
        else:
            # For SQLite: store as JSON string
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []  # Default to empty list
        if dialect.name == 'postgresql':
            return value if isinstance(value, list) else []
        else:
            # For SQLite: parse JSON string
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []
