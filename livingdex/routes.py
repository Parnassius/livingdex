from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
import aiohttp_sse
from aiohttp import web

from livingdex import app_keys
from livingdex.game_data import GameData

routes = web.RouteTableDef()


@routes.get("/")
async def index(request: web.Request) -> web.StreamResponse:
    first_game_id = next(iter(request.app[app_keys.games].keys()))
    loc = request.app.router["game"].url_for(game_id=first_game_id)
    raise web.HTTPFound(loc)


@routes.get("/{game_id}", name="game")
@aiohttp_jinja2.template("game.html")
async def game(request: web.Request) -> Mapping[str, Any]:
    game_id = request.match_info["game_id"]
    all_games = request.app[app_keys.games]
    if game_id not in all_games:
        raise web.HTTPNotFound

    game = all_games[game_id]

    return {
        "current_game": game.name,
        "current_game_id": game_id,
        "all_games": all_games,
        "expected_data": game.expected,
        "game_data": game.data,
        "gb_gbc": game.gb_gbc,
        "timestamp": max(x.timestamp for x in all_games.values()),
    }


@routes.get("/sse/{game_id}/{timestamp}", name="sse")
async def sse(request: web.Request) -> web.StreamResponse:
    async with aiohttp_sse.sse_response(request) as stream:
        game_id = request.match_info["game_id"]
        if stream.last_event_id:
            timestamp = int(stream.last_event_id.partition("-")[0])
        else:
            timestamp = int(request.match_info["timestamp"])
        request.app[app_keys.sse_streams][stream] = game_id
        try:
            async with asyncio.TaskGroup() as tg:
                for game in request.app[app_keys.games].values():
                    if game.timestamp > timestamp:
                        tg.create_task(
                            send_sse_updates(request.app, game, {(stream, game_id)})
                        )
            await stream.wait()

        finally:
            del request.app[app_keys.sse_streams][stream]

    return stream


async def _send_update(
    stream: aiohttp_sse.EventSourceResponse, msg: str, timestamp: int, event: str
) -> None:
    try:
        await stream.send(msg, f"{timestamp}-{event}", event)
    except OSError as e:
        print(e)


async def send_sse_updates(
    app: web.Application,
    game: GameData,
    streams: set[tuple[aiohttp_sse.EventSourceResponse, str]] | None = None,
) -> None:
    if streams is None:
        streams = set(app[app_keys.sse_streams].items())
    async with asyncio.TaskGroup() as tg:
        for stream, game_id in streams:
            tg.create_task(
                _send_update(
                    stream,
                    f"{game.game_id}|{game.caught}|{game.total}",
                    game.timestamp,
                    "caught",
                )
            )
            if game_id == game.game_id:
                tg.create_task(
                    _send_update(stream, game.json_data, game.timestamp, "boxes")
                )
