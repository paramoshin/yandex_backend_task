SHELL := /usr/bin/env bash

PYTHON_VERSION := $(shell python -c "import sys;t='{v[0]}.{v[1]}'.format(v=list(sys.version_info[:2]));sys.stdout.write(t)");


.PHONY: get-poetry
get-poetry:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
	source ~/.poetry/env

.PHONY: install
install:
	poetry install
	pip install nox
	poetry run pre-commit install

.PHONY: safety
safety:
	poetry run pip check
	nox -rs safety-$(PYTHON_VERSION)

.PHONY: pytest
pytest:
	PYTHONPATH=ecommerce_analyzer/ nox -rs tests

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: docs
docs:
	PYTHONPATH=ecommerce_analyzer/ nox -rs docs-$(PYTHON_VERSION)

.PHONY: loadtest
loadtest:
	PYTHONPATH=ecommerce_analyzer/ locust -f locustfile.py

.PHONY: up
up:
	DOMAIN=localhost docker-compose up -d
	docker-compose run analyzer alembic upgrade head

.PHONY: build
build:
	docker-compose -f docker-compose.yml build

.PHONY: push
push:
	docker-compose -f docker-compose.yml push

.PHONY: deploy
deploy:
	docker network create --driver=overlay traefik-public || true
	docker stack deploy -c docker-compose.yml --with-registry-auth ecommerce-analyzer
