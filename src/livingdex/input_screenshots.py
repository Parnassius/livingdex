import functools
import itertools
import json
from abc import abstractmethod
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from threading import Event

import watchfiles
from PIL import Image, ImageChops, ImageFile

from livingdex.dotnet import PKHeX
from livingdex.game_data import GameData
from livingdex.pkm import PKM


class InputScreenshots:
    def __init__(
        self, base_path: Path, games: dict[str, GameData], stop_event: Event
    ) -> None:
        self.base_path = base_path
        self.input_path = base_path / "input_screenshots"
        self.unnamed_path = self.input_path / "unnamed"

        self.game_icons = GameIcons(base_path, self.input_path, self.unnamed_path)
        self.box_numbers = BoxNumbers(base_path, self.input_path, self.unnamed_path)
        self.box_sprites = BoxSprites(base_path, self.input_path, self.unnamed_path)

        self.games = games

        self.stop_event = stop_event

        self.load_all()
        self.setup_watches()

    def load_all(self) -> None:
        for f in sorted(self.input_path.glob("*.jpg")):
            if self.stop_event.is_set():
                return

            with Image.open(f) as im:
                game_icon = self.game_icons.identify(im, f.stem)
                if game_icon is None:
                    continue

                box_number = self.box_numbers.identify(im, f.stem)
                if box_number is None or not box_number.isdecimal():
                    continue

                game = next(x for x in self.games.values() if x.save_dir == game_icon)
                box_id = int(box_number) - 1
                try:
                    expected = game.expected[box_id]
                except IndexError:
                    expected = []
                box_sprites, perfect_matches = self.box_sprites.identify_all(
                    im, game_icon, box_id, expected
                )

            if box_id < len(game.expected):
                (game.save_path / f"{box_number}.json").write_text(
                    json.dumps(box_sprites), encoding="utf-8"
                )

            if perfect_matches:
                f.unlink()

        if self.unnamed_path.is_dir():
            for subdir in self.unnamed_path.iterdir():
                with suppress(OSError):
                    subdir.rmdir()
            with suppress(OSError):
                self.unnamed_path.rmdir()

    def setup_watches(self) -> None:
        for changes in watchfiles.watch(
            self.input_path,
            watch_filter=lambda _, x: (
                not Path(x).resolve().is_relative_to(self.unnamed_path)
            ),
            stop_event=self.stop_event,
        ):
            classes: set[BaseSprites] = set()
            for _, file in changes:
                parent_dir = Path(file).parent
                if parent_dir == self.game_icons.sprites_path:
                    classes.add(self.game_icons)
                elif parent_dir == self.box_numbers.sprites_path:
                    classes.add(self.box_numbers)
                elif parent_dir == self.box_sprites.sprites_path:
                    classes.add(self.box_sprites)

            for cls in classes:
                with suppress(AttributeError):
                    delattr(cls, "sprites")
            self.load_all()


class BaseSprites:
    dir_name: str

    sprite_coords: tuple[int, int, int, int]
    sprite_max_distance: int
    sprite_loose_match: bool = True

    def __init__(self, base_path: Path, input_path: Path, unnamed_path: Path) -> None:
        self.base_path = base_path
        self.sprites_path = input_path / self.dir_name
        self.unnamed_sprites_path = unnamed_path / self.dir_name

    def _get_sprite_distance(self, im: Image.Image, im2: Image.Image) -> int:
        differences = [ImageChops.difference(im, im2).getdata()]
        if self.sprite_loose_match:
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


class SingleSprites(BaseSprites):
    @functools.cached_property
    def sprites(self) -> dict[str, ImageFile.ImageFile]:
        sprites = {}
        for f in self.sprites_path.glob("*.png"):
            name = f.stem
            if self._check_sprite_name(name):
                with Image.open(f) as im:
                    im.load()
                    sprites[f.stem] = im
            else:
                f.unlink()

        return sprites

    @abstractmethod
    def _check_sprite_name(self, name: str) -> bool: ...

    def identify(self, im: Image.Image, name: str) -> str | None:
        im = im.crop(self.sprite_coords)

        matching = {}
        for key, val in self.sprites.items():
            distance = self._get_sprite_distance(im, val)
            if distance < self.sprite_max_distance:
                matching[key] = distance
        if matching:
            return min(matching.keys(), key=lambda x: matching[x])

        self.unnamed_sprites_path.mkdir(parents=True, exist_ok=True)
        im.save(self.unnamed_sprites_path / f"{name}.png")

        return None


class GameIcons(SingleSprites):
    dir_name = "game_icons"

    sprite_coords = (1185, 512, 1227, 554)
    sprite_max_distance = 4096

    def _check_sprite_name(self, name: str) -> bool:
        return (self.base_path / name).is_dir()


class BoxNumbers(SingleSprites):
    dir_name = "box_numbers"

    sprite_coords = (1095, 522, 1124, 541)
    sprite_max_distance = 2048
    sprite_loose_match = False

    def _check_sprite_name(self, name: str) -> bool:
        try:
            int(name)
        except ValueError:
            return False
        else:
            return True


class BoxSprites(BaseSprites):
    dir_name = "box_sprites"

    box_rows = 5
    box_cols = 6

    sprite_coords = (684, 128, 760, 204)
    sprite_max_distance = 4096

    offset_x = 92
    offset_y = 76

    @functools.cached_property
    def sprites(self) -> dict[tuple[int, int, int], list[ImageFile.ImageFile]]:
        sprites = defaultdict[tuple[int, int, int], list[ImageFile.ImageFile]](list)
        for f in self.sprites_path.glob("*.png"):
            if key := self._get_sprite_key(f.stem):
                with Image.open(f) as im:
                    im.load()
                    sprites[key].append(im)
            else:
                f.unlink()

        return sprites

    def _get_sprite_key(self, name: str) -> tuple[int, int, int] | None:
        if name == "empty":
            return (0, 0, 0)
        if name == "egg":
            return (-1, 0, 0)

        parts = name.split("_")
        try:
            species = next(
                i
                for i, x in enumerate(PKHeX.Core.GameInfo.Strings.Species)
                if x == parts[0]
            )
        except StopIteration:
            return None

        if len(parts) >= 2 and parts[1] in ("m", "f"):
            del parts[1]
        form = int(parts[1]) if len(parts) >= 2 else 0
        form_argument = int(parts[2]) if len(parts) >= 3 else 0

        return (species, form, form_argument)

    def identify_all(
        self, im: Image.Image, game_icon: str, box_id: int, expected: list[PKM]
    ) -> tuple[list[tuple[int, int, int] | None], bool]:
        data = []
        perfect_matches = True

        x1, y1, x2, y2 = self.sprite_coords
        for row in range(self.box_rows):
            offset_y = self.offset_y * row
            for col in range(self.box_cols):
                offset_x = self.offset_x * col
                slot_id = row * self.box_cols + col
                coords = (
                    x1 + offset_x,
                    y1 + offset_y,
                    x2 + offset_x,
                    y2 + offset_y,
                )
                try:
                    expected_key = expected[slot_id].key
                except IndexError:
                    expected_key = (0, 0, 0)
                key, perfect_match = self._identify(
                    im.crop(coords), game_icon, box_id, slot_id, expected_key
                )
                if not perfect_match:
                    perfect_matches = False
                data.append(key)

        return data, perfect_matches

    def _identify(
        self,
        im: Image.Image,
        game_icon: str,
        box_id: int,
        slot_id: int,
        expected_key: tuple[int, int, int],
    ) -> tuple[tuple[int, int, int] | None, bool]:
        all_sprites_path = self.sprites_path / "all" / game_icon
        all_sprites_path.mkdir(parents=True, exist_ok=True)
        im.save(all_sprites_path / f"{box_id + 1}-{slot_id + 1}.png")

        if (
            expected_key
            and expected_key in self.sprites
            and any(
                self._get_sprite_distance(im, pkm_im) < self.sprite_max_distance
                for pkm_im in self.sprites[expected_key]
            )
        ):
            return expected_key, True

        matching = {}
        for key, pkm_ims in self.sprites.items():
            distance = min(self._get_sprite_distance(im, pkm_im) for pkm_im in pkm_ims)
            if distance < self.sprite_max_distance * 2:
                matching[key] = distance
        if matching:
            best_match, best_match_distance = min(matching.items(), key=lambda x: x[1])
            if (
                expected_key
                and expected_key in matching
                and matching[expected_key] < best_match_distance * 2
            ):
                return expected_key, True
            return best_match, False

        self.unnamed_sprites_path.mkdir(parents=True, exist_ok=True)
        im.save(
            self.unnamed_sprites_path / f"{game_icon}-{box_id + 1}-{slot_id + 1}.png"
        )

        return None, False
