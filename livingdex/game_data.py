from __future__ import annotations

import functools
import json
import time
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import cast

from livingdex import parsers


@dataclass(kw_only=True)
class GameData:
    game_id: str
    name: str
    base_path: InitVar[Path]
    save: InitVar[str]
    save_path: Path = field(init=False)
    parser: str
    expected: list[list[str]]
    _data: list[list[str]] | None = None
    _timestamp: int | None = None

    def __post_init__(self, base_path: Path, save: str) -> None:
        self.save_path = base_path / save

    @functools.cached_property
    def gb_gbc(self) -> bool:
        return self.parser.partition("-")[0] in ("gen1", "gen2")

    @functools.cached_property
    def caught(self) -> int:
        return sum(
            1
            for box_id, box in enumerate(self.expected)
            for pokemon_id, pokemon in enumerate(box)
            if len(self.data) > box_id
            and len(self.data[box_id]) > pokemon_id
            and pokemon == self.data[box_id][pokemon_id]
        )

    @functools.cached_property
    def total(self) -> int:
        return sum(len(x) for x in self.expected)

    @functools.cached_property
    def json_data(self) -> str:
        data = []
        for box_id, box in enumerate(self.expected):
            box_data = []
            for pokemon_id, pokemon in enumerate(box):
                if (
                    len(self.data) > box_id
                    and len(self.data[box_id]) > pokemon_id
                    and self.data[box_id][pokemon_id] != ""
                ):
                    if pokemon == self.data[box_id][pokemon_id]:
                        box_data.append("caught")
                    else:
                        box_data.append(f"wrong|{self.data[box_id][pokemon_id]}")
                else:
                    box_data.append("missing")
            data.append(box_data)

        return json.dumps(data)

    @property
    def data(self) -> list[list[str]]:
        if self._data is None:
            self.load_data()
            self._data = cast(list[list[str]], self._data)
        return self._data

    @property
    def timestamp(self) -> int:
        if self._timestamp is None:
            self.load_data()
            self._timestamp = cast(int, self._timestamp)
        return self._timestamp

    def load_data(self) -> None:
        self._data = parsers.parse(self.parser, self.save_path)
        if hasattr(self, "caught"):
            del self.caught
        if hasattr(self, "total"):
            del self.total
        if hasattr(self, "json_data"):
            del self.json_data
        self._timestamp = int(time.time())
