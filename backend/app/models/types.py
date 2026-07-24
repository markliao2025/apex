"""Custom SQLAlchemy type decorator for UUID columns."""

from typing import Any
import uuid

from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's ``UUID`` type when available, falling back to
    ``CHAR(36)`` on other databases.
    """

    impl = uuid.UUID
    cache_ok = True

    @property
    def python_type(self):
        return uuid.UUID

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return value
        elif not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value

    def process_literal_param(self, value: Any, dialect):
        return value

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return value
        return str(value)
