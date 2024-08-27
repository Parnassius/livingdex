from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from aiohttp import web


class GameData(TypedDict):
    name: str
    save: str
    parser: str
    expected: list[list[str]]


data_path = web.AppKey("data_path", Path)
games = web.AppKey("games", dict[str, GameData])
