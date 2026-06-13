import asyncio
import weakref
from pathlib import Path

import aiohttp_sse
from aiohttp import web

from livingdex.game_data import GameData

data_path = web.AppKey("data_path", Path)
games = web.AppKey("games", dict[str, GameData])
sse_streams = web.AppKey(
    "sse_streams", weakref.WeakKeyDictionary[aiohttp_sse.EventSourceResponse, str]
)
watches_task = web.AppKey("watches_task", asyncio.Task[None])
