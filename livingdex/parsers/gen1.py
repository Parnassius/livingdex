from __future__ import annotations

import os
from pathlib import Path


def parse(save: Path) -> list[list[str]] | None:
    size = save.stat().st_size
    if size < 0x8000 or size > 0x8030:
        return None

    boxes = []
    with save.open("rb") as f:
        # Check if the current box is a valid pokemon list
        f.seek(0x30C0)
        pokemon_count = f.read(1)[0]
        if pokemon_count > 20:
            return None
        f.seek(pokemon_count, os.SEEK_CUR)
        if f.read(1) != b"\xff":
            return None

        f.seek(0x284C)
        current_box = f.read(1)[0] & 0x7F
        for box_index in range(12):
            if box_index == current_box:
                ofs = 0x30C0
            else:
                ofs = 0x4000 if box_index < 6 else 0x6000
                ofs += 0x462 * (box_index % 6)
            f.seek(ofs)
            pokemon_count = f.read(1)[0]
            boxes.append([_indices[i] for i in f.read(pokemon_count)])

    return boxes


_indices = {
    0x01: "rhydon",
    0x02: "kangaskhan",
    0x03: "nidoran-m",
    0x04: "clefairy",
    0x05: "spearow",
    0x06: "voltorb",
    0x07: "nidoking",
    0x08: "slowbro",
    0x09: "ivysaur",
    0x0A: "exeggutor",
    0x0B: "lickitung",
    0x0C: "exeggcute",
    0x0D: "grimer",
    0x0E: "gengar",
    0x0F: "nidoran-f",
    0x10: "nidoqueen",
    0x11: "cubone",
    0x12: "rhyhorn",
    0x13: "lapras",
    0x14: "arcanine",
    0x15: "mew",
    0x16: "gyarados",
    0x17: "shellder",
    0x18: "tentacool",
    0x19: "gastly",
    0x1A: "scyther",
    0x1B: "staryu",
    0x1C: "blastoise",
    0x1D: "pinsir",
    0x1E: "tangela",
    0x21: "growlithe",
    0x22: "onix",
    0x23: "fearow",
    0x24: "pidgey",
    0x25: "slowpoke",
    0x26: "kadabra",
    0x27: "graveler",
    0x28: "chansey",
    0x29: "machoke",
    0x2A: "mr-mime",
    0x2B: "hitmonlee",
    0x2C: "hitmonchan",
    0x2D: "arbok",
    0x2E: "parasect",
    0x2F: "psyduck",
    0x30: "drowzee",
    0x31: "golem",
    0x33: "magmar",
    0x35: "electabuzz",
    0x36: "magneton",
    0x37: "koffing",
    0x39: "mankey",
    0x3A: "seel",
    0x3B: "diglett",
    0x3C: "tauros",
    0x40: "farfetchd",
    0x41: "venonat",
    0x42: "dragonite",
    0x46: "doduo",
    0x47: "poliwag",
    0x48: "jynx",
    0x49: "moltres",
    0x4A: "articuno",
    0x4B: "zapdos",
    0x4C: "ditto",
    0x4D: "meowth",
    0x4E: "krabby",
    0x52: "vulpix",
    0x53: "ninetales",
    0x54: "pikachu",
    0x55: "raichu",
    0x58: "dratini",
    0x59: "dragonair",
    0x5A: "kabuto",
    0x5B: "kabutops",
    0x5C: "horsea",
    0x5D: "seadra",
    0x60: "sandshrew",
    0x61: "sandslash",
    0x62: "omanyte",
    0x63: "omastar",
    0x64: "jigglypuff",
    0x65: "wigglytuff",
    0x66: "eevee",
    0x67: "flareon",
    0x68: "jolteon",
    0x69: "vaporeon",
    0x6A: "machop",
    0x6B: "zubat",
    0x6C: "ekans",
    0x6D: "paras",
    0x6E: "poliwhirl",
    0x6F: "poliwrath",
    0x70: "weedle",
    0x71: "kakuna",
    0x72: "beedrill",
    0x74: "dodrio",
    0x75: "primeape",
    0x76: "dugtrio",
    0x77: "venomoth",
    0x78: "dewgong",
    0x7B: "caterpie",
    0x7C: "metapod",
    0x7D: "butterfree",
    0x7E: "machamp",
    0x80: "golduck",
    0x81: "hypno",
    0x82: "golbat",
    0x83: "mewtwo",
    0x84: "snorlax",
    0x85: "magikarp",
    0x88: "muk",
    0x8A: "kingler",
    0x8B: "cloyster",
    0x8D: "electrode",
    0x8E: "clefable",
    0x8F: "weezing",
    0x90: "persian",
    0x91: "marowak",
    0x93: "haunter",
    0x94: "abra",
    0x95: "alakazam",
    0x96: "pidgeotto",
    0x97: "pidgeot",
    0x98: "starmie",
    0x99: "bulbasaur",
    0x9A: "venusaur",
    0x9B: "tentacruel",
    0x9D: "goldeen",
    0x9E: "seaking",
    0xA3: "ponyta",
    0xA4: "rapidash",
    0xA5: "rattata",
    0xA6: "raticate",
    0xA7: "nidorino",
    0xA8: "nidorina",
    0xA9: "geodude",
    0xAA: "porygon",
    0xAB: "aerodactyl",
    0xAD: "magnemite",
    0xB0: "charmander",
    0xB1: "squirtle",
    0xB2: "charmeleon",
    0xB3: "wartortle",
    0xB4: "charizard",
    0xB9: "oddish",
    0xBA: "gloom",
    0xBB: "vileplume",
    0xBC: "bellsprout",
    0xBD: "weepinbell",
    0xBE: "victreebel",
}
