import functools
import hashlib
import itertools
import json
import math
from abc import abstractmethod
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageChops

from livingdex.pkhex import PKHeX
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

        for species in range(1, personal.MaxSpeciesID + 1):
            if not personal.IsSpeciesInGame(species):
                continue
            form0 = PKM(self, species, 0)
            if form0.is_form_valid(0):
                data.extend(form0.forms_with_arguments)
            for form in range(1, len(form0.all_forms)):
                if form0.is_form_valid(form) and not form0.ignore_alternate_forms:
                    data.extend(PKM(self, species, form).forms_with_arguments)

        sections = {
            PKHeX.Core.SAV8SWSH: ["PokeDexIndex", "ArmorDexIndex", "CrownDexIndex"],
            PKHeX.Core.SAV8LA: ["DexIndexHisui"],
            PKHeX.Core.SAV9SV: ["DexPaldea", "DexKitakami", "DexBlueberry"],
        }

        if type(self._save_file) in sections:
            dexes = sections[type(self._save_file)]
            data_regional_dexes: dict[str, list[PKM]] = {dex: [] for dex in dexes}
            data_other = []
            for pkm in data:
                for dex in dexes:
                    if getattr(personal[pkm.species, pkm.form], dex, None):
                        data_regional_dexes[dex].append(pkm)
                        break
                else:
                    data_other.append(pkm)

            total_boxes = sum(
                math.ceil(len(data) / self.box_slot_count)
                for data in (*data_regional_dexes.values(), data_other)
            )
            data = []
            for dex in dexes:
                data_regional_dexes[dex].sort(key=lambda x: x.dex_order(dex))
                data.extend(data_regional_dexes[dex])
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
        return PKHeX.Core.SaveUtil.GetVariantSAV(str(self._game_path))

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


class ScreenshotsGameInfo(GameInfo):
    box_rows = 5
    box_cols = 6

    box_first_sprite_coords = (684, 128, 760, 204)
    box_sprites_offset_x = 92
    box_sprites_offset_y = 76

    box_sprite_max_distance = 4096

    def __init__(  # type: ignore[no-any-unimported]
        self,
        base_path: Path,
        game_path: Path,
        skipped_pokemon: list[tuple[PKHeX.Core.Species, int]],
        *,
        game_version: PKHeX.Core.GameVersion,
        box_count: int,
    ) -> None:
        self.game_version = game_version
        self.box_count = box_count

        self._cache_path = game_path / "cache"
        self._game_box_sprites_path = game_path / "box_sprites"
        self._box_sprites_path = base_path / "input_screenshots" / "box_sprites"
        self._unnamed_box_sprites_path = self._box_sprites_path / "unnamed"

        self._cache_path.mkdir(parents=True, exist_ok=True)
        self._game_box_sprites_path.mkdir(parents=True, exist_ok=True)
        self._unnamed_box_sprites_path.mkdir(parents=True, exist_ok=True)

        self._unknown_slot = PKM(self, 0, 0, is_unknown=True)

        super().__init__(base_path, game_path, skipped_pokemon)

    def _load_save_file(self) -> PKHeX.Core.SaveFile:  # type: ignore[no-any-unimported]
        return PKHeX.Core.SaveUtil.GetBlankSAV(self.game_version, "")

    @property
    def box_slot_count(self) -> int:
        return self.box_rows * self.box_cols

    @functools.cached_property
    def _sprites(self) -> dict[PKM, list[Image.Image]]:
        data = defaultdict(list)
        for f in self._box_sprites_path.glob("*.png"):
            if f.stem == "empty":
                species = 0
                form = 0
                form_argument = 0
                is_egg = False
            elif f.stem == "egg":
                species = 0
                form = 0
                form_argument = 0
                is_egg = True
            else:
                parts = f.stem.split("_")
                try:
                    species = next(
                        i
                        for i, x in enumerate(PKHeX.Core.GameInfo.Strings.Species)
                        if x == parts[0]
                    )
                except StopIteration:
                    f.unlink()
                    continue
                if len(parts) >= 2 and parts[1] in ("m", "f"):
                    del parts[1]
                form = int(parts[1]) if len(parts) >= 2 else 0
                form_argument = int(parts[2]) if len(parts) >= 3 else 0
                is_egg = False
            pkm = PKM(self, species, form, form_argument, is_egg)

            if pkm.form >= len(pkm.all_forms) or (
                pkm.form_argument and pkm.form_argument >= len(pkm.all_form_arguments)
            ):
                f.unlink()
                continue

            with Image.open(f) as im:
                im.load()
                data[pkm].append(im)

        return data

    @functools.cached_property
    def party_data(self) -> list[PKM]:
        return []

    @functools.cached_property
    def box_data(self) -> list[list[PKM]]:
        data = []
        for box_id in range(self.box_count):
            screenshot_path = self._game_path / f"{box_id + 1}.jpg"
            if not screenshot_path.is_file():
                data.append([self._empty_slot] * self.box_slot_count)
                continue

            with screenshot_path.open("rb") as f:
                screenshot_digest = hashlib.file_digest(f, "sha256").hexdigest()
            box_sprites = sorted(x.stem for x in self._box_sprites_path.glob("*.png"))
            box_sprites_digest = hashlib.sha256(
                ":".join(box_sprites).encode()
            ).hexdigest()

            cached_data = None
            json_cache_path = self._cache_path / f"{box_id + 1}.json"
            try:
                with json_cache_path.open("r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            else:
                if screenshot_digest == cache["screenshot_digest"]:
                    cached_data = [PKM(self, **params) for params in cache["data"]]
                    if box_sprites_digest == cache["box_sprites_digest"]:
                        data.append(cached_data)
                        continue

            with Image.open(screenshot_path) as im:
                parsed_box_data = self._parse_box_data(im, box_id, cached_data)

            data.append(parsed_box_data)
            cache = {
                "screenshot_digest": screenshot_digest,
                "box_sprites_digest": box_sprites_digest,
                "data": [pkm.to_dict() for pkm in parsed_box_data],
            }
            with json_cache_path.open("w", encoding="utf-8") as f:
                json.dump(cache, f)

        return data

    def _parse_box_data(
        self, im: Image.Image, box_id: int, cached_data: list[PKM] | None
    ) -> list[PKM]:
        data = []

        x1, y1, x2, y2 = self.box_first_sprite_coords
        for row in range(self.box_rows):
            offset_y = self.box_sprites_offset_y * row
            for col in range(self.box_cols):
                if cached_data:
                    cached_pkm = cached_data[row * self.box_cols + col]
                    if not cached_pkm.is_unknown:
                        data.append(cached_pkm)
                        continue
                offset_x = self.box_sprites_offset_x * col
                coords = (
                    x1 + offset_x,
                    y1 + offset_y,
                    x2 + offset_x,
                    y2 + offset_y,
                )
                data.append(
                    self._parse_box_sprite(
                        im.crop(coords), box_id, row * self.box_cols + col
                    )
                )

        return data

    def _parse_box_sprite(self, im: Image.Image, box_id: int, slot_id: int) -> PKM:
        im.save(self._game_box_sprites_path / f"{box_id + 1}-{slot_id + 1}.png")

        try:
            expected_pkm = self.boxable_forms[box_id][slot_id]
        except IndexError:
            expected_pkm = self._empty_slot

        if expected_pkm in self._sprites and any(
            _get_sprite_distance(im, pkm_im) < self.box_sprite_max_distance
            for pkm_im in self._sprites[expected_pkm]
        ):
            return expected_pkm

        matching_pkm = {}
        for pkm, pkm_ims in self._sprites.items():
            distance = min(_get_sprite_distance(im, pkm_im) for pkm_im in pkm_ims)
            if distance < self.box_sprite_max_distance:
                matching_pkm[pkm] = distance
        if matching_pkm:
            best_match_pkm, best_match_distance = min(
                matching_pkm.items(), key=lambda x: x[1]
            )
            if (
                expected_pkm in matching_pkm
                and matching_pkm[expected_pkm] < best_match_distance * 2
            ):
                return expected_pkm
            return best_match_pkm

        im.save(
            self._unnamed_box_sprites_path
            / f"{self._game_path.stem}-{box_id + 1}-{slot_id + 1}.png"
        )
        return self._unknown_slot


class InputScreenshots:
    game_icon_coords = (1185, 512, 1227, 554)
    game_icon_max_distance = 4096

    box_number_coords = (1095, 522, 1124, 541)
    box_number_max_distance = 2048

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._input_path = base_path / "input_screenshots"
        self._game_icons_path = self._input_path / "game_icons"
        self._unnamed_game_icons_path = self._game_icons_path / "unnamed"
        self._box_numbers_path = self._input_path / "box_numbers"
        self._unnamed_box_numbers_path = self._box_numbers_path / "unnamed"

        self._unnamed_game_icons_path.mkdir(parents=True, exist_ok=True)
        self._unnamed_box_numbers_path.mkdir(parents=True, exist_ok=True)

    @functools.cached_property
    def _game_icons(self) -> dict[str, Image.Image]:
        data = {}
        for f in self._game_icons_path.glob("*.png"):
            if not (self._base_path / f.stem).is_dir():
                f.unlink()
            else:
                with Image.open(f) as im:
                    im.load()
                    data[f.stem] = im

        return data

    @functools.cached_property
    def _box_numbers(self) -> dict[int, Image.Image]:
        data = {}
        for f in self._box_numbers_path.glob("*.png"):
            try:
                num = int(f.stem)
            except ValueError:
                f.unlink()
            else:
                with Image.open(f) as im:
                    im.load()
                    data[num] = im

        return data

    def load(self) -> None:
        for f in sorted(self._input_path.glob("*.jpg")):
            with Image.open(f) as im:
                game = self._parse_game_icon(im.crop(self.game_icon_coords), f.stem)
                box_number = self._parse_box_number(
                    im.crop(self.box_number_coords), f.stem
                )
            if game and box_number:
                f.replace(self._base_path / game / f"{box_number}.jpg")

    def _parse_game_icon(self, im: Image.Image, name: str) -> str | None:
        matching_games = {}
        for game, icon_im in self._game_icons.items():
            distance = _get_sprite_distance(im, icon_im)
            if distance < self.game_icon_max_distance:
                matching_games[game] = distance
        if matching_games:
            return min(matching_games.keys(), key=lambda x: matching_games[x])

        im.save(self._unnamed_game_icons_path / f"{name}.png")
        return None

    def _parse_box_number(self, im: Image.Image, name: str) -> int | None:
        matching_numbers = {}
        for number, number_im in self._box_numbers.items():
            distance = _get_sprite_distance(im, number_im, False)
            if distance < self.box_number_max_distance:
                matching_numbers[number] = distance
        if matching_numbers:
            return min(matching_numbers.keys(), key=lambda x: matching_numbers[x])

        im.save(self._unnamed_box_numbers_path / f"{name}.png")
        return None


def _get_sprite_distance(
    im: Image.Image, im2: Image.Image, loose_match: bool = True
) -> int:
    differences = [ImageChops.difference(im, im2).getdata()]
    if loose_match:
        for trans_x, trans_y in itertools.product([-1, 0, 1], repeat=2):
            if trans_x != 0 or trans_y != 0:
                differences.append(
                    ImageChops.difference(
                        im,
                        im2.transform(
                            im2.size,
                            Image.Transform.AFFINE,
                            (1, 0, trans_x, 0, 1, trans_y),
                        ),
                    ).getdata()
                )

    return sum(
        min(r // 8 + g // 8 + b // 8 for r, g, b in pixels)
        for pixels in zip(*differences, strict=True)
    )


_games: dict[str, tuple[PKHeX.Core.GameVersion, int]] = {  # type: ignore[no-any-unimported]
    "scarlet_violet": (PKHeX.Core.GameVersion.SV, 32),
}


def load(  # type: ignore[no-any-unimported]
    base_path: Path,
    save_path: Path,
    skipped_pokemon: list[tuple[PKHeX.Core.Species, int]],
) -> GameInfo:
    if save_path.is_file():
        game_info: GameInfo = PKHeXGameInfo(base_path, save_path, skipped_pokemon)
    else:
        game = (save_path / "game_id").read_text()
        game_version, box_count = _games[game.strip()]
        game_info = ScreenshotsGameInfo(
            base_path,
            save_path,
            skipped_pokemon,
            game_version=game_version,
            box_count=box_count,
        )

    # Pre-cache all cached properties
    for attr in dir(game_info):
        if isinstance(getattr(type(game_info), attr, None), functools.cached_property):
            getattr(game_info, attr)

    return game_info
