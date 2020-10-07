"""Contains application's dependencies."""
from ecommerce_analyzer.analyzer import Analyzer
from ecommerce_analyzer.db.settings import DataBaseSettings

db_settings = DataBaseSettings()
dsn = db_settings.dsn()
analyzer = Analyzer(dsn=dsn)
