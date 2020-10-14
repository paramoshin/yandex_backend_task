"""Module with Analyzer class that implements database CRUD operations and high-level business logic."""
__all__ = ["save_import", "get_citizens", "get_birthdays", "get_age_statistics", "patch_citizen"]
from .analyzer import get_age_statistics, get_birthdays, get_citizens, patch_citizen, save_import
