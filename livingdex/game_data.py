from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import cast

from livingdex import parsers


@dataclass(kw_only=True)
class GameData:
    name: str
    base_path: InitVar[Path]
    save: InitVar[str]
    save_path: Path = field(init=False)
    parser: str
    expected: list[list[str]]
    _data: list[list[str]] | None = None

    def __post_init__(self, base_path: Path, save: str) -> None:
        self.save_path = base_path / save

    @property
    def gb_gbc(self) -> bool:
        return self.parser.partition("-")[0] in ("gen1", "gen2")

    @property
    def caught(self) -> int:
        return sum(
            1
            for box_id, box in enumerate(self.expected)
            for pokemon_id, pokemon in enumerate(box)
            if len(self.data) > box_id
            and len(self.data[box_id]) > pokemon_id
            and pokemon == self.data[box_id][pokemon_id]
        )

    @property
    def total(self) -> int:
        return sum(len(x) for x in self.expected)

    @property
    def data(self) -> list[list[str]]:
        if self._data is None:
            self.load_data()
            self._data = cast(list[list[str]], self._data)
        return self._data

    def load_data(self) -> None:
        self._data = parsers.parse(self.parser, self.save_path)
