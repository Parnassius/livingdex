import copy
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Self

from livingdex.pkhex.core import PKHeX

if TYPE_CHECKING:
    from livingdex.pkhex import PKHeXWrapper


class PKM:
    def __init__(
        self,
        save: "PKHeXWrapper",
        species: int,
        form: int,
        is_egg: bool = False,
        box_id: int | None = None,
    ) -> None:
        self.save = save

        self.species = species
        self._form = form
        self.form_argument = 0
        self.is_egg = is_egg

        self.box_id = box_id

    @classmethod
    def from_pkhex(  # type: ignore[misc]
        cls, save: "PKHeXWrapper", pkm: PKHeX.Core.PKM, box_id: int | None = None
    ) -> Self:
        return cls(save, pkm.Species, pkm.Form, pkm.IsEgg, box_id=box_id)

    @property
    def form(self) -> int:
        if self.ignore_alternate_forms:
            return 0

        if PKHeX.Core.Species(self.species) == PKHeX.Core.Species.Zygarde:
            if self._form == 2:  # 10%
                return 1
            if self._form == 3:  # 50%
                return 0

        return self._form

    @property
    def species_name(self) -> str:
        return PKHeX.Core.GameInfo.Strings.Species[self.species]

    @property
    def form_name(self) -> str:
        form = self.all_forms[self.form]
        if PKHeX.Core.Species(self.species) == PKHeX.Core.Species.Alcremie:
            form += f" {PKHeX.Core.AlcremieDecoration(self.form_argument)}"
        return form

    @property
    def only_form(self) -> bool:
        return not any(
            x.species == self.species and x.form != self.form
            for box in self.save.boxable_forms
            for x in box
        )

    @property
    def ignore_alternate_forms(self) -> bool:
        ignored_species = [
            PKHeX.Core.Species.Mothim,  # The form is not cleared on evolution
            PKHeX.Core.Species.Arceus,  # Plates
            PKHeX.Core.Species.Genesect,  # Drives
            PKHeX.Core.Species.Greninja,  # Battle Bond
            PKHeX.Core.Species.Scatterbug,  # Pattern for Vivillon
            PKHeX.Core.Species.Spewpa,  # Pattern for Vivillon
            PKHeX.Core.Species.Rockruff,  # Own Tempo
            PKHeX.Core.Species.Silvally,  # Memories
            PKHeX.Core.Species.Koraidon,  # Builds
            PKHeX.Core.Species.Miraidon,  # Modes
        ]
        if self.save.save_file.Generation == 3:
            # Only one form is available, depending on the game being played
            ignored_species.append(PKHeX.Core.Species.Deoxys)
        if self.save.save_file.Generation <= 6:
            # Alternate forms revert to the default one when deposited in the PC
            ignored_species.extend(
                [
                    PKHeX.Core.Species.Shaymin,
                    PKHeX.Core.Species.Furfrou,
                    PKHeX.Core.Species.Hoopa,
                ]
            )
        return PKHeX.Core.Species(self.species) in ignored_species

    def is_form_valid(self, form: int) -> bool:
        if (
            not self.save.save_file.Personal.IsPresentInGame(self.species, form)
            or PKHeX.Core.FormInfo.IsBattleOnlyForm(
                self.species, form, self.save.save_file.Generation
            )
            or PKHeX.Core.FormInfo.IsUntradable(
                self.species, form, 0, self.save.save_file.Generation
            )
            or PKHeX.Core.FormInfo.IsTotemForm(
                self.species, form, self.save.save_file.Context
            )
        ):
            return False

        species = PKHeX.Core.Species(self.species)
        if species == PKHeX.Core.Species.Floette and form == 5:
            # Floette Eternal Flower, never released
            return False
        if species == PKHeX.Core.Species.Zygarde and form in (2, 3):
            # Power Construct forms, they are aliased to the Aura Break ones
            return False
        if (
            species == PKHeX.Core.Species.Magearna
            and form == 1
            and self.save.save_file.Generation <= 7
        ):
            # Magearna Original Color, unreleased before Generation 8
            return False

        transfer_only_species = []
        if self.save.save_file.Context == PKHeX.Core.EntityContext.Gen8:
            transfer_only_species = [
                PKHeX.Core.Species.Diancie,
                PKHeX.Core.Species.Magearna,
                PKHeX.Core.Species.Zeraora,
                PKHeX.Core.Species.Meltan,
                PKHeX.Core.Species.Melmetal,
            ]

        if species in transfer_only_species:
            return False

        return True

    @property
    def all_forms(self) -> Sequence[str]:
        strings = PKHeX.Core.GameInfo.Strings
        return PKHeX.Core.FormConverter.GetFormList(
            self.species,
            strings.Types,
            strings.forms,
            PKHeX.Core.GameInfo.GenderSymbolUnicode,
            self.save.save_file.Context,
        )

    @property
    def forms_with_arguments(self) -> Iterable[Self]:
        yield self

        if PKHeX.Core.Species(self.species) == PKHeX.Core.Species.Alcremie:
            for form_argument in range(
                PKHeX.Core.FormArgumentUtil.GetFormArgumentMax(
                    self.species, self.form, self.save.save_file.Context
                )
            ):
                new_form = copy.copy(self)
                new_form.form_argument = form_argument + 1
                yield new_form

    def evolves_from(self, other: "PKM") -> bool:
        if other.is_egg:
            return False
        tree = PKHeX.Core.EvolutionTree.GetEvolutionTree(self.save.save_file.Context)
        return any(
            PKM(self.save, pre.Item1, pre.Item2) == other
            for pre in tree.Reverse.GetPreEvolutions(self.species, self.form)
        )

    def __str__(self) -> str:
        if not self:
            return ""
        if self.is_egg:
            return "Egg"
        name = self.species_name
        if not self.only_form and not self.ignore_alternate_forms and self.form_name:
            name += f" {self.form_name}"
        return name

    def __repr__(self) -> str:
        cls = type(self)
        return (
            f"{cls.__module__}.{cls.__qualname__}"
            f"({self.save!r}, {self.species!r}, {self.form!r}, {self.is_egg!r})"
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
        return (self.species, self.form)


class LGPEStarterPKM(PKM):
    def __init__(self, save: "PKHeXWrapper") -> None:
        super().__init__(save, 0, 0)

    def __str__(self) -> str:
        return "Starter"

    def __repr__(self) -> str:
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__}({self.save!r})"

    def __bool__(self) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PKM):
            return NotImplemented
        if type(other) is type(self):
            return True
        return (PKHeX.Core.Species(other.species), other.form) in (
            (PKHeX.Core.Species.Pikachu, 8),
            (PKHeX.Core.Species.Eevee, 1),
        )
