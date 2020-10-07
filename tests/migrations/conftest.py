import pytest
from alembic.script import ScriptDirectory


@pytest.fixture(scope="module")
def revisions(alembic_config):
    revisions_dir = ScriptDirectory.from_config(alembic_config)
    revisions = list(revisions_dir.walk_revisions("base", "heads"))
    revisions.reverse()
    return revisions
