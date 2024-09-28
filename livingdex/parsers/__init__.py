from __future__ import annotations

from pathlib import Path

from livingdex.parsers import gen1, gen2, gen3, gen4, gen5


def parse(save: Path) -> list[list[str]]:
    parsers = [
        gen1.parse,
        gen2.parse,
        gen3.parse,
        gen4.parse,
        gen5.parse,
    ]

    for parser in parsers:
        if (data := parser(save)) is not None:
            return data

    raise NotImplementedError
