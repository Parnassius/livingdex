import copy
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Self

from livingdex.pkhex import PKHeX

if TYPE_CHECKING:
    from livingdex.game_info import GameInfo


class PKM:
    def __init__(
        self,
        game_info: "GameInfo",
        species: int,
        form: int,
        form_argument: int = 0,
        is_egg: bool = False,
        is_unknown: bool = False,
    ) -> None:
        self.game_info = game_info

        self.species = species
        self._form = form
        self._form_argument = form_argument
        self.is_egg = is_egg
        self.is_unknown = is_unknown

    @classmethod
    def from_pkhex(  # type: ignore[no-any-unimported]
        cls, game_info: "GameInfo", pkm: PKHeX.Core.PKM
    ) -> Self:
        return cls(
            game_info,
            pkm.Species,
            pkm.Form,
            pkm.FormArgument if isinstance(pkm, PKHeX.Core.IFormArgument) else 0,
            pkm.IsEgg,
        )

    def to_dict(self) -> dict[str, Any] | None:
        return {
            "species": self.species,
            "form": self._form,
            "form_argument": self._form_argument,
            "is_egg": self.is_egg,
            "is_unknown": self.is_unknown,
        }

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
    def form_argument(self) -> int:
        if self.all_form_arguments:
            return self._form_argument
        return 0

    @property
    def species_name(self) -> str:
        return PKHeX.Core.GameInfo.Strings.Species[self.species]  # type: ignore[no-any-return]

    @property
    def form_name(self) -> str:
        form = self.all_forms[self.form]
        if form_arguments := self.all_form_arguments:
            form += f" {form_arguments[self.form_argument]}"
        return form

    @property
    def only_form(self) -> bool:
        return not any(
            x.species == self.species and x.form != self.form
            for box in self.game_info.boxable_forms
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
        if self.game_info.generation == 3:
            # Only one form is available, depending on the game being played
            ignored_species.append(PKHeX.Core.Species.Deoxys)
        if self.game_info.generation <= 6:
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
            not self.game_info.personal.IsPresentInGame(self.species, form)
            or PKHeX.Core.FormInfo.IsBattleOnlyForm(
                self.species, form, self.game_info.generation
            )
            or PKHeX.Core.FormInfo.IsFusedForm(
                self.species, form, self.game_info.generation
            )
            or PKHeX.Core.FormInfo.IsTotemForm(
                self.species, form, self.game_info.context
            )
            or PKHeX.Core.FormInfo.IsLordForm(
                self.species, form, self.game_info.context
            )
        ):
            return False

        if (
            self.game_info.context == PKHeX.Core.EntityContext.Gen7b
            and LGPEStarterPKM.is_starter(self.species, form)
        ):
            return False

        species = PKHeX.Core.Species(self.species)
        skipped_pokemon = [
            *self.game_info.skipped_pokemon,
            (PKHeX.Core.Species.Floette, 5),  # Floette Eternal Flower, never released
            (PKHeX.Core.Species.Zygarde, 2),  # Power Construct forms, they are aliased
            (PKHeX.Core.Species.Zygarde, 3),  # to the Aura Break ones
        ]
        if self.game_info.generation <= 7:
            # Magearna Original Color, unreleased before Generation 8
            skipped_pokemon.append((PKHeX.Core.Species.Magearna, 1))

        return (species, form) not in skipped_pokemon

    @property
    def all_forms(self) -> Sequence[str]:
        strings = PKHeX.Core.GameInfo.Strings
        return PKHeX.Core.FormConverter.GetFormList(  # type: ignore[no-any-return]
            self.species,
            strings.Types,
            strings.forms,
            PKHeX.Core.GameInfo.GenderSymbolUnicode,
            self.game_info.context,
        )

    @property
    def all_form_arguments(self) -> Sequence[str]:
        arguments_enums = {
            PKHeX.Core.Species.Alcremie: PKHeX.Core.AlcremieDecoration,
        }
        species = PKHeX.Core.Species(self.species)
        if species in arguments_enums:
            enum = arguments_enums[species]
            return enum.GetNames(enum)  # type: ignore[no-any-return]
        return []

    @property
    def forms_with_arguments(self) -> Iterable[Self]:
        yield self

        if self.all_form_arguments:
            for form_argument in range(
                PKHeX.Core.FormArgumentUtil.GetFormArgumentMax(
                    self.species, self.form, self.game_info.context
                )
            ):
                new_form = copy.copy(self)
                new_form._form_argument = form_argument + 1  # noqa: SLF001
                yield new_form

    def dex_order(self, dex_attribute: str) -> tuple[int, int]:
        info = self.game_info.personal[self.species, self.form]

        is_local = False
        if info.IsRegionalForm:
            is_local = info.RegionalFormIndex == info.LocalFormIndex
        elif self.game_info.context == PKHeX.Core.EntityContext.Gen8:
            is_local = (
                # Some regional forms don't have the IsRegionalForm flag set
                (PKHeX.Core.Species(self.species), self.form)
                in [
                    (PKHeX.Core.Species.Weezing, 1),
                    (PKHeX.Core.Species.Stunfisk, 1),
                    (PKHeX.Core.Species.Articuno, 1),
                    (PKHeX.Core.Species.Zapdos, 1),
                    (PKHeX.Core.Species.Moltres, 1),
                ]
            )
        elif self.game_info.context == PKHeX.Core.EntityContext.Gen8a:
            is_local = (
                # Sneasel is the only Pokemon with more than one regional form
                PKHeX.Core.Species(self.species) == PKHeX.Core.Species.Sneasel
                and self.form == 1
            )

        return (getattr(info, dex_attribute), 0 if is_local else 1)

    def evolves_from(self, other: "PKM") -> bool:
        if self.is_egg or other.is_egg or self.is_unknown or other.is_unknown:
            return False
        tree = PKHeX.Core.EvolutionTree.GetEvolutionTree(self.game_info.context)
        return any(
            PKM(self.game_info, pre.Item1, pre.Item2) == other
            for pre in tree.Reverse.GetPreEvolutions(self.species, self.form)
        )

    def __str__(self) -> str:
        if self.is_unknown:
            return "Unknown"
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
            f"({self.game_info!r}, {self.species!r}, {self.form!r}, "
            f"{self.is_egg!r}, {self.is_unknown!r})"
        )

    def __bool__(self) -> bool:
        return self.species != 0 or self.is_unknown

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)

    @property
    def _key(self) -> tuple[int, int, int]:
        if self.is_egg:
            return (-1, 0, 0)
        if self.is_unknown:
            return (-2, 0, 0)
        return (self.species, self.form, self.form_argument)


class LGPEStarterPKM(PKM):
    def __init__(self, game_info: "GameInfo") -> None:
        super().__init__(game_info, 0, 0)

    def __str__(self) -> str:
        return "Starter"

    def __repr__(self) -> str:
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__}({self.game_info!r})"

    def __bool__(self) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PKM):
            return NotImplemented
        if type(other) is type(self):
            return True
        if other.is_egg or other.is_unknown:
            return False
        return self.is_starter(other.species, other.form)

    @staticmethod
    def is_starter(species: int, form: int) -> bool:
        return (PKHeX.Core.Species(species), form) in (
            (PKHeX.Core.Species.Pikachu, 8),
            (PKHeX.Core.Species.Eevee, 1),
        )
