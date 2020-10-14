

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

### Testing, formatting, linting, etc.
All commands are set up in makefile for easy usage.

1. Run safety checks:
```bash
make safety
```
2. Run tests:
* Unittests:
    ```bash
    make pytest
    ```
3. Run pre-commit hooks (include `black`, `isort`, `pyupgrade`, `flakehell` and `mypy`) on all files:
```bash
make lint
```
4. Create beautiful html documentation from your code:
```bash
make docs
```

---
# TODO:
- ansible deploy
