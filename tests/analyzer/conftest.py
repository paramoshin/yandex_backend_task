import pytest
from alembic import command
from ecommerce_analyzer.analyzer import Analyzer


@pytest.fixture(scope="module")
def analyzer(db_settings):
    return Analyzer(dsn=db_settings.dsn())


@pytest.fixture(scope="module")
def migrated_postgres(alembic_config, postgres):
    command.upgrade(alembic_config, "head")
