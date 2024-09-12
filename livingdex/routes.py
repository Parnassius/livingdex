from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from livingdex import app_keys, parsers

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

    game_data = parsers.parse(
        all_games[game_id]["parser"],
        request.app[app_keys.data_path] / all_games[game_id]["save"],
    )
    gb_gbc = all_games[game_id]["parser"].partition("-")[0] in ("gen1", "gen2")

    return {
        "current_game": all_games[game_id]["name"],
        "current_game_id": game_id,
        "all_games": {k: v["name"] for k, v in all_games.items()},
        "expected_data": all_games[game_id]["expected"],
        "game_data": game_data,
        "gb_gbc": gb_gbc,
    }
