import functools
import itertools
from pathlib import Path

from livingdex.pkhex.core import PKHeX
from livingdex.pkhex.pkm import PKM as PKM


class PKHeXWrapper:
    def __init__(self, save_path: Path) -> None:
        self.save_file = PKHeX.Core.SaveUtil.GetVariantSAV(str(save_path))

    @property
    def box_slot_count(self) -> int:
        if self.save_file is None:
            return 30

        return self.save_file.BoxSlotCount

    @property
    def box_data(self) -> list[list[PKM]]:
        if self.save_file is None:
            return []

        return [
            [PKM.from_pkhex(self, pkm) for pkm in self.save_file.GetBoxData(box_id)]
            for box_id in range(self.save_file.BoxCount)
        ]

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
            data.append(form0)
            for form in range(1, len(form0.all_forms)):
                if (
                    personal.IsPresentInGame(species, form)
                    and not PKHeX.Core.FormInfo.IsBattleOnlyForm(
                        species, form, self.save_file.Generation
                    )
                    and not form0.ignore_alternate_forms
                    and not form0.is_form_unobtainable(form)
                ):
                    data.append(PKM(self, species, form))

        return [list(x) for x in itertools.batched(data, self.save_file.BoxSlotCount)]
