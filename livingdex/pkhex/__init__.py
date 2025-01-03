import functools
import itertools
from pathlib import Path

from livingdex.pkhex.core import PKHeX
from livingdex.pkhex.pkm import PKM as PKM
from livingdex.pkhex.pkm import LGPEStarterPKM


class PKHeXWrapper:
    def __init__(self, save_path: Path) -> None:
        self.save_path = save_path
        self.save_file = PKHeX.Core.SaveUtil.GetVariantSAV(str(save_path))

    @property
    def box_slot_count(self) -> int:
        if self.save_file is None:
            return 30

        if isinstance(self.save_file, PKHeX.Core.SAV7b):
            return 6  # Single box with 6 columns

        return self.save_file.BoxSlotCount

    @property
    def box_data(self) -> list[list[PKM]]:
        if self.save_file is None:
            return []

        return self._flatten_lgpe_boxes(
            [
                [PKM.from_pkhex(self, pkm) for pkm in self.save_file.GetBoxData(box_id)]
                for box_id in range(self.save_file.BoxCount)
            ],
            False,
        )

    @property
    def party_data(self) -> list[PKM]:
        if self.save_file is None:
            return []

        return [PKM.from_pkhex(self, pkm) for pkm in self.save_file.PartyData]

    @functools.cached_property
    def boxable_forms(self) -> list[list[PKM]]:
        if self.save_file is None:
            return []

        data = []
        personal = self.save_file.Personal
        for species in range(1, personal.MaxSpeciesID + 1):
            if not personal.IsSpeciesInGame(species):
                continue
            form0 = PKM(self, species, 0)
            if form0.is_form_valid(0):
                data.append(form0)
            for form in range(1, len(form0.all_forms)):
                if form0.is_form_valid(form) and not form0.ignore_alternate_forms:
                    data.append(PKM(self, species, form))

        return self._flatten_lgpe_boxes(
            [list(x) for x in itertools.batched(data, self.save_file.BoxSlotCount)],
            True,
        )

    def _flatten_lgpe_boxes(
        self, data: list[list[PKM]], boxable_forms: bool
    ) -> list[list[PKM]]:
        if isinstance(self.save_file, PKHeX.Core.SAV7b):
            data = [[x for box in data for x in box]]
            if boxable_forms:
                data[0].insert(0, LGPEStarterPKM(self))

        return data
