FROM python:3.13-alpine3.21 as base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATA_PATH=/data
WORKDIR /app

RUN apk add --no-cache dotnet8-runtime


FROM base as builder

RUN apk add --no-cache gcc musl-dev libffi-dev
RUN apk add --no-cache dotnet8-sdk

RUN python -m venv /opt/poetry-venv
RUN /opt/poetry-venv/bin/pip install --upgrade pip setuptools
RUN /opt/poetry-venv/bin/pip install poetry

RUN python -m venv .venv

COPY poetry.lock pyproject.toml .
RUN /opt/poetry-venv/bin/poetry install --no-interaction --only main --no-root

COPY . .
RUN /opt/poetry-venv/bin/poetry build --no-interaction --format wheel
RUN .venv/bin/pip install --no-deps ./dist/*.whl

RUN dotnet restore --packages nuget
RUN cp nuget/pkhex.core/*/lib/net*/PKHeX.Core.dll .venv/lib/python*/site-packages


FROM builder as test

RUN apk add --no-cache nodejs npm

RUN /opt/poetry-venv/bin/poetry install --no-interaction --no-root
RUN npm ci

RUN /opt/poetry-venv/bin/poetry run poe ruff-format --check
RUN /opt/poetry-venv/bin/poetry run poe prettier-check
RUN /opt/poetry-venv/bin/poetry run poe mypy
RUN /opt/poetry-venv/bin/poetry run poe ruff
RUN /opt/poetry-venv/bin/poetry run poe biome
RUN /opt/poetry-venv/bin/poetry run poe pytest


FROM base as final

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv .venv
COPY ./entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
