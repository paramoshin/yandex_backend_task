import pytest
from alembic import command
from ecommerce_analyzer.analyzer import Analyzer
from ecommerce_analyzer.api.application import analyzer as original_analyzer
from ecommerce_analyzer.api.application import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def analyzer(db_settings):
    return Analyzer(dsn=db_settings.dsn())


@pytest.fixture(scope="module")
def migrated_postgres(alembic_config, postgres):
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="module")
def client(analyzer):
    client = TestClient(app)
    app.dependency_overrides[original_analyzer] = analyzer
    return client
