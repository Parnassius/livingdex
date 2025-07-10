from livingdex.game_info.base import ScreenshotsGameInfo
from livingdex.pkhex import PKHeX


class ScarletVioletGameInfo(ScreenshotsGameInfo):
    game_version = PKHeX.Core.GameVersion.SV
    box_count = 32

    box_first_sprite_coords = (451, 200, 569, 318)
    box_sprites_offset_x = 126
    box_sprites_offset_y = 126
