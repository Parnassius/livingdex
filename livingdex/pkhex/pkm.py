from __future__ import annotations

from collections.abc import Sequence

from livingdex.pkhex.core import PKHeX


class PKM:
    def __init__(
        self,
        context: PKHeX.Core.EntityContext,
        species: int,
        form: int,
        is_egg: bool = False,
    ) -> None:
        self.context = context

        self.species = species
        self.form = form
        self.is_egg = is_egg

        self.only_form = False

    @property
    def species_name(self) -> str:
        return PKHeX.Core.GameInfo.Strings.Species[self.species]

    @property
    def form_name(self) -> str:
        return self.all_forms[self.form]

    @property
    def ignore_alternate_forms(self) -> bool:
        ignored_species = [
            PKHeX.Core.Species.Mothim,  # The form is not cleared on evolution
            PKHeX.Core.Species.Arceus,  # Plates
            PKHeX.Core.Species.Kyurem,  # Fusions
            PKHeX.Core.Species.Genesect,  # Drives
            PKHeX.Core.Species.Greninja,  # Battle Bond
            PKHeX.Core.Species.Scatterbug,  # Pattern for Vivillon
            PKHeX.Core.Species.Spewpa,  # Pattern for Vivillon
            PKHeX.Core.Species.Rockruff,  # Own Tempo
            PKHeX.Core.Species.Silvally,  # Memories
            PKHeX.Core.Species.Necrozma,  # Fusions
            PKHeX.Core.Species.Calyrex,  # Fusions
        ]
        if self.context == PKHeX.Core.EntityContext.Gen3:
            # Only one form is available, depending on the game being played
            ignored_species.append(PKHeX.Core.Species.Deoxys)
        if self.context <= PKHeX.Core.EntityContext.Gen6:
            # Alternate forms revert to the default one when deposited in the PC
            ignored_species.extend(
                [
                    PKHeX.Core.Species.Shaymin,
                    PKHeX.Core.Species.Furfrou,
                    PKHeX.Core.Species.Hoopa,
                ]
            )
        return PKHeX.Core.Species(self.species) in ignored_species

    def is_form_unobtainable(self, form: int | None = None) -> bool:
        species = PKHeX.Core.Species(self.species)
        form = form or self.form
        if self.context == PKHeX.Core.EntityContext.Gen7b and (species, form) in (
            (PKHeX.Core.Species.Pikachu, 8),
            (PKHeX.Core.Species.Eevee, 1),
        ):
            # Pikachu/Eevee Starter
            # Not really unobtainable but they can't be traded to the other game
            return True
        if species == PKHeX.Core.Species.Floette and form == 5:
            # Floette Eternal Flower, never released
            return True
        return False

    @property
    def all_forms(self) -> Sequence[str]:
        strings = PKHeX.Core.GameInfo.Strings
        return PKHeX.Core.FormConverter.GetFormList(
            self.species,
            strings.Types,
            strings.forms,
            PKHeX.Core.GameInfo.GenderSymbolUnicode,
            self.context,
        )

    def __str__(self) -> str:
        if not self:
            return ""
        if self.is_egg:
            return "Egg"
        name = self.species_name
        if (
            not self.only_form
            and not self.ignore_alternate_forms
            and not self.is_form_unobtainable()
            and self.form_name
        ):
            name += f" {self.form_name}"
        return name

    def __repr__(self) -> str:
        cls = type(self)
        return (
            f"{cls.__module__}.{cls.__qualname__}"
            f"({self.context!r}, {self.species!r}, {self.form!r}, {self.is_egg!r})"
        )

    def __bool__(self) -> bool:
        return self.species != 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)

    @property
    def _key(self) -> tuple[int, int]:
        if self.is_egg:
            return (-1, 0)
        return self.species, (self.form if not self.ignore_alternate_forms else 0)
