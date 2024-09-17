from __future__ import annotations

import asyncio

from aiohttp import web

from livingdex.game_data import GameData

games = web.AppKey("games", dict[str, GameData])
watches_task = web.AppKey("watches_task", asyncio.Task[None])
