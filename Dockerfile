FROM python:3.8-slim-buster as builder

ENV PIP_NO_CACHE_DIR=off \
  POETRY_VERSION=1.0.10

RUN apt-get update && \
  apt-get -y --no-install-recommends install gcc build-essential python3-dev libpq-dev

WORKDIR ecommerce_analyzer/
COPY pyproject.toml poetry.lock ./

ARG DEV_MODE=false

RUN pip install "poetry==1.0.10" && \
  poetry config virtualenvs.in-project true && \
  poetry install --no-dev --no-interaction --no-ansi --no-root

FROM python:3.8-slim-buster

WORKDIR ecommerce_analyzer/

COPY --from=builder /ecommerce_analyzer /ecommerce_analyzer
COPY /ecommerce_analyzer ./

ENV VIRTUAL_ENV=/ecommerce_analyzer/.venv
ENV PATH="$PATH:$VIRTUAL_ENV/bin"
ENV PYTHONPATH="/ecommerce_analyzer"

ARG DEV_MODE
RUN if [ "$DEV_MODE" = "true" ]; \
  then mv /ecommerce_analyzer/env/dev.env /ecommerce_analyzer/env/.env && \
   alembic upgrade head; \
  fi

CMD ["uvicorn", "api.application:app", "--host", "0.0.0.0", "--port", "80"]
