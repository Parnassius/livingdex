import asyncio
import functools
import json
import time
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from livingdex import game_info
from livingdex.pkhex import PKHeX

if TYPE_CHECKING:
    from livingdex.pkm import PKM


class GameData:
    def __init__(
        self,
        game_id: str,
        name: str,
        base_path: Path,
        save: str,
        other_saves: list[str] | None = None,
        skipped_pokemon: list[list[int]] | None = None,
    ) -> None:
        self.game_id = game_id
        self.name = name

        self.base_path = base_path
        self.save_path = (base_path / save).resolve()
        if other_saves is None:
            self.other_saves_paths = []
        else:
            self.other_saves_paths = [(base_path / x).resolve() for x in other_saves]

        if skipped_pokemon is None:
            self.skipped_pokemon = []
        else:
            self.skipped_pokemon = [
                (PKHeX.Core.Species(species), form) for species, form in skipped_pokemon
            ]

        self.box_size: int
        self.expected: list[list[PKM]]
        self.data: list[list[PKM]]
        self.other_saves_data: dict[PKM, str]
        self.timestamp: int

        self._load_data(*self._load_game_info())

    @functools.cached_property
    def caught(self) -> int:
        return sum(
            1
            for box_id, box in enumerate(self.expected)
            for pokemon_id, pokemon in enumerate(box)
            if pokemon
            and len(self.data) > box_id
            and len(self.data[box_id]) > pokemon_id
            and pokemon == self.data[box_id][pokemon_id]
        )

    @functools.cached_property
    def total(self) -> int:
        return sum(1 for box in self.expected for pokemon in box if pokemon)

    @functools.cached_property
    def json_data(self) -> str:
        data = []
        for box_id, box in enumerate(self.expected):
            box_data = []
            for pokemon_id, pokemon in enumerate(box):
                if pokemon:
                    data_pokemon = self.data[box_id][pokemon_id]
                    if (
                        len(self.data) > box_id
                        and len(self.data[box_id]) > pokemon_id
                        and data_pokemon
                    ):
                        if pokemon == data_pokemon:
                            box_data.append("caught")
                        elif pokemon.evolves_from(data_pokemon):
                            box_data.append(f"evo|{data_pokemon}")
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
                else:
                    box_data.append("filler")
            data.append(box_data)

        return json.dumps(data)

    async def load_data(self) -> None:
        save, other_saves = await asyncio.to_thread(self._load_game_info)
        self._load_data(save, other_saves)

    def _load_data(
        self, save: game_info.GameInfo, other_saves: dict[str, game_info.GameInfo]
    ) -> None:
        self.box_size = save.box_slot_count

        self.expected = save.boxable_forms

        self.data = save.box_data
        self.other_saves_data = {}
        self._load_other_save_data(save, self.save_path.stem, main_save=True)
        for save_name, other_save in other_saves.items():
            self._load_other_save_data(other_save, save_name)

        for attr in dir(self):
            if isinstance(getattr(type(self), attr, None), functools.cached_property):
                with suppress(AttributeError):
                    delattr(self, attr)

        self.timestamp = int(time.time())

    def _load_other_save_data(
        self, save: game_info.GameInfo, name: str, *, main_save: bool = False
    ) -> None:
        for box_number, box_data in enumerate((save.party_data, *save.box_data)):
            pokemon_location = "Party" if box_number == 0 else f"Box {box_number}"
            for pokemon in box_data:
                if pokemon and pokemon not in self.other_saves_data:
                    if not main_save:
                        pokemon_location = f"{name} ({pokemon_location})"
                    self.other_saves_data[pokemon] = pokemon_location

    def _load_game_info(
        self,
    ) -> tuple[game_info.GameInfo, dict[str, game_info.GameInfo]]:
        save = game_info.load(self.base_path, self.save_path, self.skipped_pokemon)
        other_saves = {
            other_save_path.stem: game_info.load(
                self.base_path, other_save_path, self.skipped_pokemon
            )
            for other_save_path in self.other_saves_paths
        }
        return save, other_saves
