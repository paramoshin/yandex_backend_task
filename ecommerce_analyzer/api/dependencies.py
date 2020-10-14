"""Contains application's dependencies."""
from databases import Database
from db.settings import DataBaseSettings

db_settings = DataBaseSettings()
dsn = db_settings.dsn()
database = Database(dsn, min_size=5, max_size=20)
