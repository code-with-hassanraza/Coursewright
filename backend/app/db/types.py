from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


class FlexibleJSON(TypeDecorator):
    """
    Uses JSONB when running against PostgreSQL (production).
    Falls back to JSON for SQLite (tests).
    SQLAlchemy calls load_dialect_impl() at table creation time
    and picks the right type automatically based on the DB engine.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())