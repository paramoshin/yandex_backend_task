"""Module that contains database models, settings and alembic migrations."""
__all__ = ["metadata", "citizens", "imports", "relations"]
from .tables import citizens, imports, metadata, relations
