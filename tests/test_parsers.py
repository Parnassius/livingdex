from __future__ import annotations

from pathlib import Path

import pytest

from livingdex.parsers import parse


@pytest.mark.parametrize(
    "parser, save_file",
    [
        ("gen1", "red.sav"),
        ("gen1", "blue.sav"),
        ("gen1", "yellow.sav"),
        ("gen2-gold-silver", "gold.sav"),
        ("gen2-gold-silver", "silver.sav"),
        ("gen2-crystal", "crystal.sav"),
        ("gen3", "ruby-slot1.sav"),
        ("gen3", "ruby-slot2.sav"),
        ("gen3", "sapphire-slot1.sav"),
        ("gen3", "sapphire-slot2.sav"),
        ("gen3", "firered-slot1.sav"),
        ("gen3", "firered-slot2.sav"),
        ("gen3", "leafgreen-slot1.sav"),
        ("gen3", "leafgreen-slot2.sav"),
        ("gen3", "emerald-slot1.sav"),
        ("gen3", "emerald-slot2.sav"),
        ("gen4-diamond-pearl", "diamond-slot1.sav"),
        ("gen4-diamond-pearl", "diamond-slot2.sav"),
        ("gen4-diamond-pearl", "pearl-slot1.sav"),
        ("gen4-diamond-pearl", "pearl-slot2.sav"),
        ("gen4-platinum", "platinum-slot1.sav"),
        ("gen4-platinum", "platinum-slot2.sav"),
        ("gen4-heartgold-soulsilver", "heartgold-slot1.sav"),
        ("gen4-heartgold-soulsilver", "heartgold-slot2.sav"),
        ("gen4-heartgold-soulsilver", "soulsilver-slot1.sav"),
        ("gen4-heartgold-soulsilver", "soulsilver-slot2.sav"),
        ("gen5", "black.sav"),
        ("gen5", "white.sav"),
        ("gen5", "black2.sav"),
        ("gen5", "white2.sav"),
    ],
)
def test_parsers(parser: str, save_file: str) -> None:
    save = Path(__file__).parent / "saves" / save_file
    with save.with_suffix(".expected").open("r", encoding="utf-8") as f:
        expected = [x.split(",") if x else [] for x in f.read().split("\n")]
    assert parse(parser, save) == expected
