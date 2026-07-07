"""Database query backends."""

from license_tracker.db.queries.base import Database
from license_tracker.db.queries.factory import create_database

__all__ = ["Database", "create_database"]
