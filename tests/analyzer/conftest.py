import pytest
from alembic import command
from databases import Database


@pytest.fixture(scope="module")
def database(db_settings):
    database = Database(db_settings.dsn())
    return database


@pytest.fixture(scope="module")
def migrated_postgres(alembic_config, postgres):
    command.upgrade(alembic_config, "head")
