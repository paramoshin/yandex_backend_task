import pytest
from alembic import command
from api.application import app
from api.application import get_db as original_db
from databases import Database
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def migrated_postgres(alembic_config, postgres):
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="function")
async def database(db_settings):
    database = Database(db_settings.dsn())
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture(scope="function")
def client(database):
    client = TestClient(app)

    def get_db():
        return database

    app.dependency_overrides[original_db] = get_db
    return client
