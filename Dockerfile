FROM python:3.8-slim-buster as builder

ENV PIP_NO_CACHE_DIR=off \
  POETRY_VERSION=1.0.10

RUN apt-get update && \
  apt-get -y --no-install-recommends install gcc build-essential python3-dev libpq-dev

WORKDIR ecommerce_analyzer/
COPY pyproject.toml poetry.lock ./

RUN pip install "poetry==1.0.10" && \
  poetry config virtualenvs.in-project true && \
  poetry install --no-dev --no-interaction --no-ansi --no-root

FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists

WORKDIR ecommerce_analyzer/

COPY --from=builder /ecommerce_analyzer /ecommerce_analyzer
COPY /ecommerce_analyzer ./
COPY /gunicorn.conf.py /gunicorn.conf.py

ENV VIRTUAL_ENV=/ecommerce_analyzer/.venv
ENV PATH="$PATH:$VIRTUAL_ENV/bin"
ENV PYTHONPATH="/ecommerce_analyzer"

EXPOSE 80

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "/gunicorn.conf.py", "api.application:app"]
