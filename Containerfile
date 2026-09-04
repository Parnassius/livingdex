FROM python:3.14-alpine as base

ENV PYTHONUNBUFFERED=1

ENV DATA_PATH=/data
WORKDIR /app

RUN --mount=type=cache,target=/etc/apk/cache \
    apk add dotnet10-runtime


FROM base as builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_NO_EDITABLE=1
ENV UV_NO_SYNC=1

RUN --mount=type=cache,target=/etc/apk/cache \
    apk add dotnet10-sdk

COPY --from=ghcr.io/astral-sh/uv /uv /bin/uv

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-dev

RUN --mount=type=cache,target=/root/.local/share/NuGet/http-cache \
    --mount=type=bind,source=packages.lock.json,target=packages.lock.json \
    --mount=type=bind,source=livingdex.csproj,target=livingdex.csproj \
    dotnet restore --packages nuget
RUN cp nuget/pkhex.core/*/lib/net*/PKHeX.Core.dll .venv/lib/python*/site-packages

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev


FROM builder as test

RUN --mount=type=cache,target=/etc/apk/cache \
    apk add nodejs npm
RUN --mount=type=cache,target=/etc/apk/cache \
    apk add make

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
RUN --mount=type=cache,target=/root/.npm \
    npm ci

RUN make lint
RUN make pytest


FROM base as final

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv .venv
COPY ./entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
