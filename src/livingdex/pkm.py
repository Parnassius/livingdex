import copy
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Self

from livingdex.dotnet import PKHeX, System

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
        self.form = form
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
            "form": self.form,
            "form_argument": self._form_argument,
            "is_egg": self.is_egg,
            "is_unknown": self.is_unknown,
        }

    @property
    def normalized_form(self) -> int:
        if self.ignore_alternate_forms:
            return 0

        species = PKHeX.Core.Species(self.species)

        if (species, self.form) in (
            (PKHeX.Core.Species.Greninja, 1),  # Battle Bond
            (PKHeX.Core.Species.Rockruff, 1),  # Own Tempo
        ):
            return 0

        if species == PKHeX.Core.Species.Zygarde:
            if self.form == 2:  # 10%
                return 1
            if self.form == 3:  # 50%
                return 0

        return self.form

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
        form = self.all_forms[self.normalized_form]
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
            PKHeX.Core.Species.Scatterbug,  # Pattern for Vivillon
            PKHeX.Core.Species.Spewpa,  # Pattern for Vivillon
            PKHeX.Core.Species.Silvally,  # Memories
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

    @property
    def is_valid(self) -> bool:
        if (
            not self.game_info.personal.IsPresentInGame(self.species, self.form)
            or PKHeX.Core.FormInfo.IsBattleOnlyForm(
                self.species, self.form, self.game_info.generation
            )
            or PKHeX.Core.FormInfo.IsFusedForm(
                self.species, self.form, self.game_info.generation
            )
            or PKHeX.Core.FormInfo.IsTotemForm(
                self.species, self.form, self.game_info.context
            )
            or not self.is_obtainable(
                allow_transfers=self.game_info.generation < 8, allow_events=True
            )
        ):
            return False

        if (
            self.game_info.context == PKHeX.Core.EntityContext.Gen7b
            and LGPEStarterPKM.is_starter(self.species, self.form)
        ):
            return False

        return (
            PKHeX.Core.Species(self.species),
            self.form,
        ) not in self.game_info.skipped_pokemon

    def is_obtainable(
        self,
        *,
        allow_transfers: bool = False,
        allow_events: bool = False,
        checked_forms: set[tuple[int, int]] | None = None,
    ) -> bool:
        if (
            self.game_info.context == PKHeX.Core.EntityContext.Gen9
            and PKHeX.Core.Species(self.species) == PKHeX.Core.Species.Gimmighoul
            and self.form == 1
        ):
            return True

        pkm = self.game_info.blank_pkm
        pkm.Species = self.species
        pkm.Form = self.form
        PKHeX.Core.GenderApplicator.SetSaneGender(pkm, None)
        if (
            self.game_info.context
            in (PKHeX.Core.EntityContext.Gen6, PKHeX.Core.EntityContext.Gen7)
            and self.species == int(PKHeX.Core.Species.Meowstic)
            and self.form == 1
        ):
            pkm.Gender = 1

        versions = []
        if not allow_transfers:
            versions = [
                x
                for x in PKHeX.Core.GameVersion.GetValues(PKHeX.Core.GameVersion)
                if PKHeX.Core.GameUtil.IsValidSavedVersion(x)
                and PKHeX.Core.EntityContextExtensions.get_Context(x)
                == self.game_info.context
            ]

        encs = list(
            PKHeX.Core.EncounterMovesetGenerator.GenerateEncounters(
                pkm, System.ReadOnlyMemory[System.UInt16]([]), *versions
            )
        )
        if not allow_events:
            non_event_encs = []
            for enc in encs:
                impl = enc.__implementation__
                if not isinstance(
                    impl, PKHeX.Core.MysteryGift | PKHeX.Core.EncounterOutbreak9
                ) and not (
                    isinstance(impl, PKHeX.Core.ITeraRaid9) and impl.IsDistribution
                ):
                    non_event_encs.append(enc)
            encs = non_event_encs

        if encs and all(
            isinstance(x.__implementation__, PKHeX.Core.IEncounterEgg) for x in encs
        ):
            if checked_forms is None:
                checked_forms = set()
            checked_forms.add((self.species, self.form))
            tree = PKHeX.Core.EvolutionTree.GetEvolutionTree(self.game_info.context)
            related = [
                (x.Item1, x.Item2)
                for x in tree.GetEvolutionsAndPreEvolutions(self.species, self.form)
                if (x.Item1, x.Item2) not in checked_forms
            ]
            other_parents = {
                (int(k1), k2): (int(v1), v2)
                for k1, k2, v1, v2 in (
                    (PKHeX.Core.Species.NidoranF, 0, PKHeX.Core.Species.NidoranM, 0),
                    (PKHeX.Core.Species.NidoranM, 0, PKHeX.Core.Species.NidoranF, 0),
                    (PKHeX.Core.Species.Volbeat, 0, PKHeX.Core.Species.Illumise, 0),
                    (PKHeX.Core.Species.Illumise, 0, PKHeX.Core.Species.Volbeat, 0),
                    (PKHeX.Core.Species.Phione, 0, PKHeX.Core.Species.Manaphy, 0),
                    (PKHeX.Core.Species.Indeedee, 0, PKHeX.Core.Species.Indeedee, 1),
                    (PKHeX.Core.Species.Indeedee, 1, PKHeX.Core.Species.Indeedee, 0),
                )
            }
            if other_parent := other_parents.get((self.species, self.form)):
                related.append(other_parent)
            return any(
                PKM(self.game_info, species, form).is_obtainable(
                    allow_transfers=allow_transfers,
                    allow_events=allow_events,
                    checked_forms=checked_forms,
                )
                for species, form in related
            )

        for enc in encs:
            species = enc.Species
            form = enc.Form
            if (
                PKHeX.Core.Species(species)
                in (
                    PKHeX.Core.Species.Scatterbug,
                    PKHeX.Core.Species.Spewpa,
                    PKHeX.Core.Species.Vivillon,
                )
                and form == PKHeX.Core.EncounterUtil.FormVivillon
                and self.form <= PKHeX.Core.Vivillon3DS.MaxWildFormID
            ) or form == PKHeX.Core.EncounterUtil.FormRandom:
                form = self.form

            if species == self.species and (
                form == self.form
                or PKHeX.Core.FormInfo.IsFormChangeable(
                    species,
                    form,
                    self.form,
                    self.game_info.context,
                    self.game_info.context,
                )
            ):
                return True

            if self.evolves_from(PKM(self.game_info, species, form)):
                return True

        return False

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

    @property
    def is_local_form(self) -> bool:
        species = PKHeX.Core.Species(self.species)
        info = self.game_info.personal[self.species, self.form]

        is_local = (
            info.RegionalFormIndex == info.LocalFormIndex
            if info.IsRegionalForm
            else False
        )

        if self.game_info.context == PKHeX.Core.EntityContext.Gen8 and (
            (species, self.form)
            in [
                (PKHeX.Core.Species.Weezing, 1),
                (PKHeX.Core.Species.Stunfisk, 1),
                (PKHeX.Core.Species.Articuno, 1),
                (PKHeX.Core.Species.Zapdos, 1),
                (PKHeX.Core.Species.Moltres, 1),
            ]
        ):
            # Sword / Shield: some regional forms don't have the IsRegionalForm flag set
            is_local = True

        if self.game_info.context == PKHeX.Core.EntityContext.Gen8a and (
            (species, self.form) == (PKHeX.Core.Species.Sneasel, 1)
        ):
            # Arceus: Sneasel is the only Pokemon with more than one regional form
            is_local = True

        if self.game_info.context == PKHeX.Core.EntityContext.Gen9a and (
            (species, self.form)
            in [
                (PKHeX.Core.Species.Farfetchd, 1),
                (PKHeX.Core.Species.Yamask, 1),
                (PKHeX.Core.Species.MrMime, 1),
            ]
        ):
            # ZA: some galarian forms are erroneously set as local
            is_local = False

        return is_local

    def evolves_from(self, other: "PKM") -> bool:
        if self.is_egg or other.is_egg or self.is_unknown or other.is_unknown:
            return False
        tree = PKHeX.Core.EvolutionTree.GetEvolutionTree(self.game_info.context)
        for pre in tree.Reverse.GetPreEvolutions(self.species, self.form):
            if pre.Item1 == other.species and (
                pre.Item2 == other.form
                or PKHeX.Core.FormInfo.IsFormChangeable(
                    pre.Item1,
                    pre.Item2,
                    other.form,
                    self.game_info.context,
                    self.game_info.context,
                )
            ):
                return True

        return False

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
        return (self.species, self.normalized_form, self.form_argument)


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
