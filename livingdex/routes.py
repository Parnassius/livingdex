from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp_jinja2
from aiohttp import web

from livingdex import app_keys

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
    }
