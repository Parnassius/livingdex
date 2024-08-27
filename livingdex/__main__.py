from __future__ import annotations

import tomllib
from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web
from typenv import Env

from livingdex import app_keys
from livingdex.routes import routes


async def add_headers(
    request: web.Request, response: web.StreamResponse  # noqa: ARG001
) -> None:
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "img-src 'self'; "
        "style-src 'self'; "
        "base-uri 'none'; "
        "form-action 'none'; "
    )


def main() -> None:
    env = Env()
    env.read_env()

    port = env.int("PORT")
    data_path = Path(__file__).parent.parent
    if data_path_ := env.str("DATA_PATH", default=""):
        data_path = Path(data_path_)

    app = web.Application()

    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader("livingdex"))
    app.add_routes(routes)

    app[aiohttp_jinja2.static_root_key] = "/static"
    app.router.add_static("/static", Path(__file__).parent / "static", name="static")

    app[app_keys.data_path] = data_path
    with (data_path / "games.toml").open("rb") as f:
        app[app_keys.games] = tomllib.load(f)

    app.on_response_prepare.append(add_headers)

    web.run_app(app, port=port)


if __name__ == "__main__":
    main()
