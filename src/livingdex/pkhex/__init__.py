import functools
import itertools
from pathlib import Path

from livingdex.pkhex.core import PKHeX
from livingdex.pkhex.pkm import PKM as PKM
from livingdex.pkhex.pkm import LGPEStarterPKM


class PKHeXWrapper:
    def __init__(self, save_path: Path) -> None:
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

        data = [
            [
                PKM.from_pkhex(self, pkm, box_id)
                for pkm in self.save_file.GetBoxData(box_id)
            ]
            for box_id in range(self.save_file.BoxCount)
        ]

        if isinstance(self.save_file, PKHeX.Core.SAV7b):
            data = [[x for box in data for x in box]]

        return data

    @property
    def party_data(self) -> list[PKM]:
        if self.save_file is None:
            return []

        return [PKM.from_pkhex(self, pkm) for pkm in self.save_file.PartyData]

    @functools.cached_property
    def boxable_forms(self) -> list[list[PKM]]:
        if self.save_file is None:
            return []

        data: list[PKM] = []
        empty_slot = PKM(self, 0, 0)
        personal = self.save_file.Personal

        if isinstance(self.save_file, PKHeX.Core.SAV7b):
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

        if type(self.save_file) in sections:
            dexes = sections[type(self.save_file)]
            data_regional_dexes: dict[str, list[PKM]] = {dex: [] for dex in dexes}
            data_other = []
            for pkm in data:
                for dex in dexes:
                    if getattr(personal[pkm.species, pkm.form], dex, None):
                        data_regional_dexes[dex].append(pkm)
                        break
                else:
                    data_other.append(pkm)
            data = []
            for dex in dexes:
                data_regional_dexes[dex].sort(key=lambda x: x.dex_order(dex))
                data.extend(data_regional_dexes[dex])
                if filled_slots := len(data) % self.box_slot_count:
                    data.extend([empty_slot] * (self.box_slot_count - filled_slots))
            data.extend(data_other)

        if filled_slots := len(data) % self.box_slot_count:
            data.extend([empty_slot] * (self.box_slot_count - filled_slots))

        if isinstance(self.save_file, PKHeX.Core.SAV7b):
            return [data]

        return [
            list(x) for x in itertools.batched(data, self.box_slot_count, strict=False)
        ]
