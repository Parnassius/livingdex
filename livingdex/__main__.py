from __future__ import annotations

import asyncio
import tomllib
from functools import partial
from pathlib import Path

import aiohttp_jinja2
import jinja2
import watchfiles
from aiohttp import web
from typenv import Env

from livingdex import app_keys
from livingdex.game_data import GameData
from livingdex.routes import routes


async def setup_file_watches(app: web.Application, *, data_path: Path) -> None:
    async def _setup_file_watches() -> None:
        async for changes in watchfiles.awatch(data_path):
            changed_files = {x[1] for x in changes}
            for game in app[app_keys.games].values():
                for file in changed_files:
                    try:
                        if game.save_path.samefile(file):
                            game.load_data()
                            break
                    except OSError:
                        pass

    app[app_keys.watches_task] = asyncio.create_task(_setup_file_watches())


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

    with (data_path / "games.toml").open("rb") as f:
        app[app_keys.games] = {
            k: GameData(**v, base_path=data_path) for k, v in tomllib.load(f).items()
        }

    app.on_startup.append(partial(setup_file_watches, data_path=data_path))

    app.on_response_prepare.append(add_headers)

    web.run_app(app, port=port)


if __name__ == "__main__":
    main()
