from __future__ import annotations

from pathlib import Path

import pytest

from livingdex import parsers


@pytest.mark.parametrize(
    "save_file",
    [
        ("red.sav"),
        ("blue.sav"),
        ("yellow.sav"),
        ("gold.sav"),
        ("silver.sav"),
        ("crystal.sav"),
        ("ruby-slot1.sav"),
        ("ruby-slot2.sav"),
        ("sapphire-slot1.sav"),
        ("sapphire-slot2.sav"),
        ("firered-slot1.sav"),
        ("firered-slot2.sav"),
        ("leafgreen-slot1.sav"),
        ("leafgreen-slot2.sav"),
        ("emerald-slot1.sav"),
        ("emerald-slot2.sav"),
        ("diamond-slot1.sav"),
        ("diamond-slot2.sav"),
        ("pearl-slot1.sav"),
        ("pearl-slot2.sav"),
        ("platinum-slot1.sav"),
        ("platinum-slot2.sav"),
        ("heartgold-slot1.sav"),
        ("heartgold-slot2.sav"),
        ("soulsilver-slot1.sav"),
        ("soulsilver-slot2.sav"),
        ("black.sav"),
        ("white.sav"),
        ("black2.sav"),
        ("white2.sav"),
        ("x.sav"),
        ("y.sav"),
        ("omegaruby.sav"),
        ("alphasapphire.sav"),
    ],
)
def test_parsers(save_file: str) -> None:
    save = Path(__file__).parent / "saves" / save_file
    with save.with_suffix(".expected").open("r", encoding="utf-8") as f:
        expected = [x.split(",") if x else [] for x in f.read().split("\n")]
    assert parsers.parse(save) == expected
