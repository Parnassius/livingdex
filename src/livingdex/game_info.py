import functools
import itertools
import json
import math
from abc import abstractmethod
from collections.abc import Callable
from pathlib import Path

from livingdex.dotnet import PKHeX
from livingdex.pkm import PKM, LGPEStarterPKM


class GameInfo:
    def __init__(  # type: ignore[no-any-unimported]
        self,
        base_path: Path,
        game_path: Path,
        skipped_pokemon: list[tuple[PKHeX.Core.Species, int]],
    ) -> None:
        self._base_path = base_path
        self._game_path = game_path
        self.skipped_pokemon = skipped_pokemon
        self._empty_slot = PKM(self, 0, 0)
        self._save_file = self._load_save_file()

    @abstractmethod
    def _load_save_file(self) -> PKHeX.Core.SaveFile: ...  # type: ignore[no-any-unimported]

    @property
    def blank_pkm(self) -> PKHeX.Core.PKM:  # type: ignore[no-any-unimported]
        return self._save_file.BlankPKM

    @property
    def generation(self) -> int:
        return self._save_file.Generation  # type: ignore[no-any-return]

    @property
    def context(self) -> PKHeX.Core.EntityContext:  # type: ignore[no-any-unimported]
        return self._save_file.Context

    @property
    def personal(self) -> PKHeX.Core.IPersonalTable:  # type: ignore[no-any-unimported]
        return self._save_file.Personal

    @property
    @abstractmethod
    def box_count(self) -> int: ...

    @property
    @abstractmethod
    def box_slot_count(self) -> int: ...

    @functools.cached_property
    @abstractmethod
    def party_data(self) -> list[PKM]: ...

    @functools.cached_property
    @abstractmethod
    def box_data(self) -> list[list[PKM]]: ...

    @functools.cached_property
    def boxable_forms(self) -> list[list[PKM]]:
        data: list[PKM] = []
        personal = self._save_file.Personal

        if isinstance(self._save_file, PKHeX.Core.SAV7b):
            data.append(LGPEStarterPKM(self))

        for species_id in range(1, personal.MaxSpeciesID + 1):
            if not personal.IsSpeciesInGame(species_id):
                continue
            form0 = PKM(self, species_id, 0)
            if form0.is_valid:
                data.extend(form0.forms_with_arguments)
            for form_id in range(1, len(form0.all_forms)):
                form = PKM(self, species_id, form_id)
                if form.is_valid and form not in data:
                    data.extend(form.forms_with_arguments)

        sections: dict[  # type: ignore[no-any-unimported]
            type[PKHeX.Core.SaveFile],
            list[str | Callable[[PKHeX.Core.PersonalInfo], int | None]],
        ] = {
            PKHeX.Core.SAV8SWSH: ["PokeDexIndex", "ArmorDexIndex", "CrownDexIndex"],
            PKHeX.Core.SAV8LA: ["DexIndexHisui"],
            PKHeX.Core.SAV9SV: ["DexPaldea", "DexKitakami", "DexBlueberry"],
            PKHeX.Core.SAV9ZA: [
                lambda x: x.DexIndex if x.IsLumioseNative else None,
                lambda x: x.DexIndex if x.IsHyperspaceNative else None,
            ],
        }

        if type(self._save_file) in sections:
            dexes = sections[type(self._save_file)]
            data_regional_dexes: list[list[tuple[int, PKM]]] = [[] for _ in dexes]
            data_other = []
            for pkm in data:
                for dex_id, dex in enumerate(dexes):
                    if isinstance(dex, str):
                        dex_index = getattr(personal[pkm.species, pkm.form], dex, None)
                    else:
                        dex_index = dex(personal[pkm.species, pkm.form])
                    if dex_index:
                        data_regional_dexes[dex_id].append((dex_index, pkm))
                        break
                else:
                    if pkm.is_obtainable():
                        data_other.append(pkm)

            total_boxes = sum(
                math.ceil(len(x) / self.box_count) for x in data_regional_dexes
            ) + math.ceil(len(data_other) / self.box_count)
            data = []
            for dex_data in data_regional_dexes:
                data.extend(
                    x
                    for _, x in sorted(
                        dex_data,
                        key=lambda x: (x[0], not x[1].is_local_form),
                    )
                )
                if total_boxes > self.box_slot_count:
                    empty_slots = 6 - len(data) % 6
                else:
                    empty_slots = self.box_slot_count - len(data) % self.box_slot_count
                if empty_slots:
                    data.extend([self._empty_slot] * empty_slots)
            data.extend(data_other)

        if filled_slots := len(data) % self.box_slot_count:
            data.extend([self._empty_slot] * (self.box_slot_count - filled_slots))

        if isinstance(self._save_file, PKHeX.Core.SAV7b):
            return [data]

        return [
            list(x) for x in itertools.batched(data, self.box_slot_count, strict=False)
        ]


class PKHeXGameInfo(GameInfo):
    def _load_save_file(self) -> PKHeX.Core.SaveFile:  # type: ignore[no-any-unimported]
        return PKHeX.Core.SaveUtil.GetSaveFile(str(self._game_path))

    @property
    def box_count(self) -> int:
        if isinstance(self._save_file, PKHeX.Core.SAV7b):
            return 1  # Single box with 6 columns

        return self._save_file.BoxCount  # type: ignore[no-any-return]

    @property
    def box_slot_count(self) -> int:
        if isinstance(self._save_file, PKHeX.Core.SAV7b):
            return 6  # Single box with 6 columns

        return self._save_file.BoxSlotCount  # type: ignore[no-any-return]

    @functools.cached_property
    def party_data(self) -> list[PKM]:
        return [PKM.from_pkhex(self, pkm) for pkm in self._save_file.PartyData]

    @functools.cached_property
    def box_data(self) -> list[list[PKM]]:
        data = [
            [PKM.from_pkhex(self, pkm) for pkm in self._save_file.GetBoxData(box_id)]
            for box_id in range(self._save_file.BoxCount)
        ]

        if isinstance(self._save_file, PKHeX.Core.SAV7b):
            data = [[x for box in data for x in box]]

        return data


class ScreenshotsGameInfo(PKHeXGameInfo):
    def __init__(  # type: ignore[no-any-unimported]
        self,
        base_path: Path,
        game_path: Path,
        skipped_pokemon: list[tuple[PKHeX.Core.Species, int]],
        *,
        game_version: PKHeX.Core.GameVersion,
    ) -> None:
        self.game_version = game_version

        self._egg_slot = PKM(self, 0, 0, is_egg=True)
        self._unknown_slot = PKM(self, 0, 0, is_unknown=True)

        super().__init__(base_path, game_path, skipped_pokemon)

    def _load_save_file(self) -> PKHeX.Core.SaveFile:  # type: ignore[no-any-unimported]
        return PKHeX.Core.BlankSaveFile.Get(self.game_version)

    @functools.cached_property
    def party_data(self) -> list[PKM]:
        return []

    @functools.cached_property
    def box_data(self) -> list[list[PKM]]:
        data = []
        for box_id in range(self.box_count):
            json_path = self._game_path / f"{box_id + 1}.json"
            if not json_path.is_file():
                data.append([self._empty_slot] * self.box_slot_count)
                continue

            box_data = []
            with json_path.open(encoding="utf-8") as f:
                for pkm_args in json.load(f):
                    if pkm_args == [0, 0, 0]:
                        box_data.append(self._empty_slot)
                    elif pkm_args == [-1, 0, 0]:
                        box_data.append(self._egg_slot)
                    elif pkm_args is None:
                        box_data.append(self._unknown_slot)
                    else:
                        box_data.append(PKM(self, *pkm_args))
            data.append(box_data)

        return data


def load(  # type: ignore[no-any-unimported]
    base_path: Path,
    save_path: Path,
    skipped_pokemon: list[tuple[PKHeX.Core.Species, int]],
) -> GameInfo:
    if save_path.is_file():
        game_info: GameInfo = PKHeXGameInfo(base_path, save_path, skipped_pokemon)
    else:
        game_version = PKHeX.Core.GameVersion.Parse(
            PKHeX.Core.GameVersion, (save_path / "game_version").read_text().strip()
        )
        game_info = ScreenshotsGameInfo(
            base_path,
            save_path,
            skipped_pokemon,
            game_version=game_version,
        )

    # Pre-cache all cached properties
    for attr in dir(game_info):
        if isinstance(getattr(type(game_info), attr, None), functools.cached_property):
            getattr(game_info, attr)

    return game_info
