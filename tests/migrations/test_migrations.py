from alembic.command import downgrade, upgrade


def test_migrations(postgres, alembic_config, revisions):
    for revision in revisions:
        upgrade(alembic_config, revision.revision)

        downgrade(alembic_config, revision.down_revision or "-1")
        upgrade(alembic_config, revision.revision)
