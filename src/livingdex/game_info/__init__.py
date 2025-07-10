import functools
from pathlib import Path

from livingdex.game_info.base import GameInfo as GameInfo
from livingdex.game_info.base import PKHeXGameInfo, ScreenshotsGameInfo
from livingdex.game_info.scarlet_violet import ScarletVioletGameInfo
from livingdex.pkhex import PKHeX

_games: dict[str, type[ScreenshotsGameInfo]] = {
    "scarlet_violet": ScarletVioletGameInfo,
}


def load(  # type: ignore[no-any-unimported]
    save_path: Path, skipped_pokemon: list[tuple[PKHeX.Core.Species, int]]
) -> GameInfo:
    if save_path.is_file():
        game_info_cls: type[GameInfo] = PKHeXGameInfo
    else:
        game = (save_path / "game_id").read_text()
        game_info_cls = _games[game.strip()]

    game_info = game_info_cls(save_path, skipped_pokemon)

    # Pre-cache all cached properties
    for attr in dir(game_info):
        if isinstance(getattr(type(game_info), attr, None), functools.cached_property):
            getattr(game_info, attr)

    return game_info
