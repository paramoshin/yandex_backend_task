"""Package-wide test fixtures."""
import socket
import uuid

import docker
import pytest
from alembic.config import Config
from config import ROOT_DIR
from db.settings import ENV_DIR, DataBaseSettings
from tzlocal import get_localzone
from utils import wait_for_pg_container

TIMEZONE = get_localzone().zone


@pytest.fixture(scope="session")
def unused_port():
    """Find unused port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def db_settings(unused_port):
    """Create dev database settings with unused port."""
    return DataBaseSettings(host="localhost", port=unused_port, _env_file=(ENV_DIR / "dev.env"))


@pytest.fixture(scope="session")
def postgres(db_settings):
    """Создает временную БД для запуска теста."""
    client = docker.from_env()
    container_id = uuid.uuid4()
    environment = dict(
        POSTGRES_PASSWORD=db_settings.password,
        POSTGRES_USER=db_settings.user,
        POSTGRES_DB=db_settings.db,
        TZ=TIMEZONE,
        PGTZ=TIMEZONE,
    )
    container = client.containers.run(
        "postgres:latest",
        command="-c fsync=off",
        name=f"test-postgres-{container_id}",
        detach=True,
        environment=environment,
        ports={"5432/tcp": db_settings.port},
        tmpfs={"/var/lib/postgresql/data": ""},
    )
    try:
        wait_for_pg_container(
            user=db_settings.user,
            password=db_settings.password,
            host=db_settings.host,
            port=db_settings.port,
            db=db_settings.db,
        )
    except RuntimeError:
        container.kill()
        container.remove(v=True)
        raise RuntimeError("Couldn't start postgres container in time")
    else:
        yield container
        container.kill()
        container.remove(v=True)


@pytest.fixture(scope="session")
def alembic_config(db_settings, postgres):
    """Создает объект с конфигурацией для alembic, настроенный на временную БД."""
    alembic_cfg = Config(ROOT_DIR / "alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_settings.dsn())
    alembic_cfg.set_main_option("script_location", str((ROOT_DIR / "db/alembic").absolute()))
    return alembic_cfg
