import functools
import itertools
import json
import time
from dataclasses import InitVar, dataclass, field
from pathlib import Path

from livingdex.pkhex import PKM, PKHeXWrapper


@dataclass(kw_only=True)
class GameData:
    game_id: str
    name: str
    base_path: InitVar[Path]
    save: InitVar[str]
    other_saves: InitVar[list[str] | None] = None
    save_path: Path = field(init=False)
    other_saves_paths: list[Path] = field(init=False)
    box_size: int = field(init=False)
    expected: list[list[PKM]] = field(init=False)
    data: list[list[PKM]] = field(init=False)
    other_saves_data: dict[PKM, str] = field(init=False)
    timestamp: int = field(init=False)

    def __post_init__(
        self, base_path: Path, save: str, other_saves: list[str] | None = None
    ) -> None:
        self.save_path = base_path / save
        if other_saves is None:
            self.other_saves_paths = []
        else:
            self.other_saves_paths = [base_path / x for x in other_saves]
        self.load_data()

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
                    and data_pokemon
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

    def load_data(self) -> None:
        save = PKHeXWrapper(self.save_path)

        self.box_size = save.box_slot_count

        self.expected = save.boxable_forms

        self.data = save.box_data
        self.other_saves_data = {}
        self._load_other_save_data(save, self.save_path.stem, main_save=True)
        for other_save_path in self.other_saves_paths:
            self._load_other_save_data(
                PKHeXWrapper(other_save_path), other_save_path.stem
            )

        for attr in dir(self):
            if isinstance(getattr(type(self), attr, None), functools.cached_property):
                try:
                    delattr(self, attr)
                except AttributeError:
                    pass

        self.timestamp = int(time.time())

    def _load_other_save_data(
        self, save: PKHeXWrapper, name: str, *, main_save: bool = False
    ) -> None:
        for pokemon in itertools.chain(save.party_data, *save.box_data):
            if pokemon and pokemon not in self.other_saves_data:
                pokemon_location = (
                    "Party" if pokemon.box_id is None else f"Box {pokemon.box_id + 1}"
                )
                if not main_save:
                    pokemon_location = f"{name} ({pokemon_location})"
                self.other_saves_data[pokemon] = pokemon_location
