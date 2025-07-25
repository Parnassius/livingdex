import asyncio
import tomllib
import weakref
from pathlib import Path

import aiohttp_jinja2
import jinja2
import watchfiles
from aiohttp import web
from typenv import Env

from livingdex import app_keys
from livingdex.game_data import GameData
from livingdex.game_info import InputScreenshots
from livingdex.routes import routes, send_sse_updates


async def setup_file_watches(app: web.Application) -> None:
    async def _setup_input_screenshots_watches() -> None:
        input_path = app[app_keys.data_path] / "input_screenshots"
        async for _ in watchfiles.awatch(input_path, recursive=False):
            try:
                await asyncio.to_thread(InputScreenshots(app[app_keys.data_path]).load)
            except OSError:
                pass

    async def _setup_box_sprites_watches() -> None:
        screenshots_games = [
            game
            for game in app[app_keys.games].values()
            if any(x.is_dir() for x in (game.save_path, *game.other_saves_paths))
        ]
        box_sprites_path = app[app_keys.data_path] / "input_screenshots" / "box_sprites"
        async for changes in watchfiles.awatch(box_sprites_path, recursive=False):
            if any(Path(x[1]).suffix == ".png" for x in changes):
                async with asyncio.TaskGroup() as tg:
                    for game in screenshots_games:
                        try:
                            await game.load_data()
                            tg.create_task(send_sse_updates(app, game))
                            break
                        except OSError:
                            pass

    async def _setup_game_files_watches() -> None:
        games = app[app_keys.games].values()
        paths = set()
        for game in games:
            paths.add(game.save_path)
            paths.update(game.other_saves_paths)
        async for changes in watchfiles.awatch(*paths, recursive=False):
            changed_files = {x[1] for x in changes}
            async with asyncio.TaskGroup() as tg:
                for game in games:
                    for file in changed_files:
                        file_path = Path(file).resolve()
                        try:
                            if any(
                                file_path.is_relative_to(x)
                                for x in (game.save_path, *game.other_saves_paths)
                            ):
                                await game.load_data()
                                tg.create_task(send_sse_updates(app, game))
                                break
                        except OSError:
                            pass

    app[app_keys.watches_tasks] = [
        asyncio.create_task(_setup_input_screenshots_watches()),
        asyncio.create_task(_setup_box_sprites_watches()),
        asyncio.create_task(_setup_game_files_watches()),
    ]


async def add_headers(
    request: web.Request,  # noqa: ARG001
    response: web.StreamResponse,
) -> None:
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "connect-src 'self'; "
        "img-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "base-uri 'none'; "
        "form-action 'none'; "
    )


async def close_sse_streams(app: web.Application) -> None:
    async with asyncio.TaskGroup() as tg:
        streams = app[app_keys.sse_streams].keys()
        for stream in set(streams):
            stream.stop_streaming()
            tg.create_task(stream.wait())


def main() -> None:
    env = Env()
    env.read_env()

    port = env.int("PORT")
    data_path = Path(__file__).parent.parent.parent
    if data_path_ := env.str("DATA_PATH", default=""):
        data_path = Path(data_path_)
    data_path = data_path.resolve()

    app = web.Application()
    app[app_keys.data_path] = data_path

    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader("livingdex"))
    app.add_routes(routes)

    app[aiohttp_jinja2.static_root_key] = "/static"
    app.router.add_static("/static", Path(__file__).parent / "static", name="static")

    InputScreenshots(data_path).load()
    with (data_path / "games.toml").open("rb") as f:
        app[app_keys.games] = {
            k: GameData(game_id=k, **v, base_path=data_path)
            for k, v in tomllib.load(f).items()
        }

    app.on_startup.append(setup_file_watches)

    app.on_response_prepare.append(add_headers)

    app[app_keys.sse_streams] = weakref.WeakKeyDictionary()
    app.on_shutdown.append(close_sse_streams)

    web.run_app(app, port=port)


if __name__ == "__main__":
    main()
