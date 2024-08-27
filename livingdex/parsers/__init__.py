from __future__ import annotations

from pathlib import Path

from livingdex.parsers import gen1, gen2, gen3, gen4


def parse(parser: str, save: Path) -> list[list[str]]:
    parser, _, sub_parser = parser.partition("-")
    return _parsers[parser](save, sub_parser)


_parsers = {
    "gen1": gen1.parse,
    "gen2": gen2.parse,
    "gen3": gen3.parse,
    "gen4": gen4.parse,
}
