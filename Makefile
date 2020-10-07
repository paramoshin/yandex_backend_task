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
	PYTHONPATH=. nox -rs tests

.PHONY: xdoctest
xdoctest:
	nox -rs xdoctest

.PHONY: tests
tests:
	PYTHONPATH=. pytest xdoctest

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: docs
docs:
	nox -rs docs-$(PYTHON_VERSION)

.PHONY: build
build:
	poetry build
