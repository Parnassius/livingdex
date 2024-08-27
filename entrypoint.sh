#!/bin/sh
set -e

if [ -d /static ]; then
    rm -rf /static/*
    cp -r /app/.venv/lib/python*/site-packages/livingdex/static/* /static
fi

exec livingdex "$@"
