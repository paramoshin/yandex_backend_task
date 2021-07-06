

<h1 align='center'>
    yandex_backend_task
</h1>

<h4 align='center'>

</h4>

<div align="center">

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/yandex_backend_task/yandex_backend_task/blob/master/.pre-commit-config.yaml)
</div>

---
Вступительное задание в Школу бэкенд-разработки Яндекса - https://disk.yandex.ru/i/dA9umaGbQdMNLw.  
Реализовано для практики

## Стэк
- [FastAPI](https://fastapi.tiangolo.com/) для веб-сервиса и сваггер схемы из коробки с [Pydantic](https://pydantic-docs.helpmanual.io/) для валидации данных
- [Gunicorn](https://gunicorn.org/) в качестве WSGI сервера
- [Postgres](https://www.postgresql.org/) в качестве БД
- [SQLAlchemy](https://www.sqlalchemy.org/) для ORM
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) для миграций
- [Databases](https://www.encode.io/databases/) для асинхронных запросов
- [Pytest](https://docs.pytest.org/en/6.2.x/) для юнит-тестов
- [Locust](https://locust.io/) для нагрузочного тестирования
- [Nox](https://nox.thea.codes/en/stable/) для управления окружением тестов
- [Poetry](https://python-poetry.org/) для управления зависимостями
- [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) и [Docker Swarm](https://docs.docker.com/engine/swarm/) для деплоя
- [Traefik](https://doc.traefik.io/traefik/) для балансировки нагрузки и https-сертификатов
- [pre-commit](https://pre-commit.com/) хуки для проверки кода


### Installing, running, testing, formatting, linting, etc.
All commands are set up in Makefile for easy usage.

1. Install dependencies
```bash
make get-poetry
make install
```
2. Run safety checks:
```bash
make safety
```
3. Run tests:
* Unit tests:
    ```bash
    make pytest
    ```
* Load test:
  ```bash
  make loadtest
  ```
4. Run pre-commit hooks (include `black`, `isort`, `pyupgrade`, `flakehell` and `mypy`) on all files:
```bash
make lint
```
5. Create documentation:
```bash
make docs
```
6. Build image:
```bash
make build
```
7. Start services:
```bash
make up
```
8. Push to container registry:
```bash
make push
```
9. Deploy docker swarm stack:
```bash
make deploy
```


---
