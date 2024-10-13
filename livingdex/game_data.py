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
    other_saves: InitVar[list[str] | None] = None
    save_path: Path = field(init=False)
    other_saves_paths: list[Path] = field(init=False)
    expected: list[list[str]]
    _data: list[list[str]] | None = None
    _other_saves_data: dict[str, str] | None = None
    _timestamp: int | None = None

    def __post_init__(
        self, base_path: Path, save: str, other_saves: list[str] | None = None
    ) -> None:
        self.save_path = base_path / save
        if other_saves is None:
            self.other_saves_paths = []
        else:
            self.other_saves_paths = [base_path / x for x in other_saves]

    @functools.cached_property
    def gb_gbc(self) -> bool:
        return len(self.data[0]) < 30

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
                data_pokemon = self.data[box_id][pokemon_id]
                if (
                    len(self.data) > box_id
                    and len(self.data[box_id]) > pokemon_id
                    and data_pokemon != ""
                ):
                    if pokemon == data_pokemon:
                        box_data.append("caught")
                    elif pokemon in self.other_saves_data:
                        box_data.append(
                            "wrong-and-other-game|"
                            f"{data_pokemon} / {self.other_saves_data[pokemon]}"
                        )
                    else:
                        box_data.append(f"wrong|{data_pokemon}")
                elif pokemon in self.other_saves_data:
                    box_data.append(f"other-game|{self.other_saves_data[pokemon]}")
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
    def other_saves_data(self) -> dict[str, str]:
        if self._other_saves_data is None:
            self.load_data()
            self._other_saves_data = cast(dict[str, str], self._other_saves_data)
        return self._other_saves_data

    @property
    def timestamp(self) -> int:
        if self._timestamp is None:
            self.load_data()
            self._timestamp = cast(int, self._timestamp)
        return self._timestamp

    def load_data(self) -> None:
        self._data = parsers.parse(self.save_path)
        self._other_saves_data = {
            x: save.stem
            for save in self.other_saves_paths
            for box in parsers.parse(save)
            for x in box
            if x != ""
        }

        if hasattr(self, "gb_gbc"):
            del self.gb_gbc
        if hasattr(self, "caught"):
            del self.caught
        if hasattr(self, "total"):
            del self.total
        if hasattr(self, "json_data"):
            del self.json_data
        self._timestamp = int(time.time())
