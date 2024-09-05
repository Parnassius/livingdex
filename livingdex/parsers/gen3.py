from __future__ import annotations

import struct
from pathlib import Path


def parse(save: Path, sub_parser: str) -> list[list[str]]:
    assert sub_parser == ""

    boxes = []
    with save.open("rb") as f:
        f.seek(0x00DFFC)
        (slot1_counter,) = struct.unpack("<L", f.read(4))
        f.seek(0x01BFFC)
        (slot2_counter,) = struct.unpack("<L", f.read(4))
        if 0xFFFFFFFF in (slot1_counter, slot2_counter):
            slot1_counter = (slot1_counter + 1) & 0xFFFFFFFF
            slot2_counter = (slot2_counter + 1) & 0xFFFFFFFF
        base_ofs = 0x000000 if slot1_counter > slot2_counter else 0x00E000

        box_buffers = [b""] * 9
        for i in range(14):
            f.seek(base_ofs + i * 0x1000 + 0x0FF4)
            (section_id,) = struct.unpack("<H", f.read(2))
            if section_id >= 5:
                f.seek(base_ofs + i * 0x1000)
                box_buffers[section_id - 5] = f.read(0x0F80)
        box_buffer = b"".join(box_buffers)[0x0004:0x8344]

        for box_index in range(14):
            box = []
            for pokemon_index in range(30):
                pokemon_data_start = ((box_index * 30) + pokemon_index) * 0x50
                pokemon_data = box_buffer[
                    pokemon_data_start : pokemon_data_start + 0x50
                ]
                if all(x == 0 for x in pokemon_data):
                    pokemon = ""
                else:
                    pid, tid, *data = struct.unpack("<LL24x12L", pokemon_data)
                    key = pid ^ tid
                    sections = _sections_positions[pid % 24]
                    is_egg = ((data[sections[3] * 3 + 1] ^ key) >> 30) & 1
                    if is_egg:
                        pokemon = "egg"
                    else:
                        pokemon = _indices[(data[sections[0] * 3] ^ key) & 0xFFFF]
                        if pokemon == "unown":
                            letter = (
                                (((pid >> 24) & 0x3) << 6)
                                + (((pid >> 16) & 0x3) << 4)
                                + (((pid >> 8) & 0x3) << 2)
                                + (pid & 0x3)
                            )
                            letters = [
                                *"abcdefghijklmnopqrstuvwxyz",
                                "exclamation",
                                "question",
                            ]
                            pokemon = f"unown-{letters[letter % 28]}"
                box.append(pokemon)
            boxes.append(box)

    return boxes


_sections_positions = [
    (0, 1, 2, 3),
    (0, 1, 3, 2),
    (0, 2, 1, 3),
    (0, 3, 1, 2),
    (0, 2, 3, 1),
    (0, 3, 2, 1),
    (1, 0, 2, 3),
    (1, 0, 3, 2),
    (2, 0, 1, 3),
    (3, 0, 1, 2),
    (2, 0, 3, 1),
    (3, 0, 2, 1),
    (1, 2, 0, 3),
    (1, 3, 0, 2),
    (2, 1, 0, 3),
    (3, 1, 0, 2),
    (2, 3, 0, 1),
    (3, 2, 0, 1),
    (1, 2, 3, 0),
    (1, 3, 2, 0),
    (2, 1, 3, 0),
    (3, 1, 2, 0),
    (2, 3, 1, 0),
    (3, 2, 1, 0),
]

_indices = {
    0x001: "bulbasaur",
    0x002: "ivysaur",
    0x003: "venusaur",
    0x004: "charmander",
    0x005: "charmeleon",
    0x006: "charizard",
    0x007: "squirtle",
    0x008: "wartortle",
    0x009: "blastoise",
    0x00A: "caterpie",
    0x00B: "metapod",
    0x00C: "butterfree",
    0x00D: "weedle",
    0x00E: "kakuna",
    0x00F: "beedrill",
    0x010: "pidgey",
    0x011: "pidgeotto",
    0x012: "pidgeot",
    0x013: "rattata",
    0x014: "raticate",
    0x015: "spearow",
    0x016: "fearow",
    0x017: "ekans",
    0x018: "arbok",
    0x019: "pikachu",
    0x01A: "raichu",
    0x01B: "sandshrew",
    0x01C: "sandslash",
    0x01D: "nidoran-f",
    0x01E: "nidorina",
    0x01F: "nidoqueen",
    0x020: "nidoran-m",
    0x021: "nidorino",
    0x022: "nidoking",
    0x023: "clefairy",
    0x024: "clefable",
    0x025: "vulpix",
    0x026: "ninetales",
    0x027: "jigglypuff",
    0x028: "wigglytuff",
    0x029: "zubat",
    0x02A: "golbat",
    0x02B: "oddish",
    0x02C: "gloom",
    0x02D: "vileplume",
    0x02E: "paras",
    0x02F: "parasect",
    0x030: "venonat",
    0x031: "venomoth",
    0x032: "diglett",
    0x033: "dugtrio",
    0x034: "meowth",
    0x035: "persian",
    0x036: "psyduck",
    0x037: "golduck",
    0x038: "mankey",
    0x039: "primeape",
    0x03A: "growlithe",
    0x03B: "arcanine",
    0x03C: "poliwag",
    0x03D: "poliwhirl",
    0x03E: "poliwrath",
    0x03F: "abra",
    0x040: "kadabra",
    0x041: "alakazam",
    0x042: "machop",
    0x043: "machoke",
    0x044: "machamp",
    0x045: "bellsprout",
    0x046: "weepinbell",
    0x047: "victreebel",
    0x048: "tentacool",
    0x049: "tentacruel",
    0x04A: "geodude",
    0x04B: "graveler",
    0x04C: "golem",
    0x04D: "ponyta",
    0x04E: "rapidash",
    0x04F: "slowpoke",
    0x050: "slowbro",
    0x051: "magnemite",
    0x052: "magneton",
    0x053: "farfetchd",
    0x054: "doduo",
    0x055: "dodrio",
    0x056: "seel",
    0x057: "dewgong",
    0x058: "grimer",
    0x059: "muk",
    0x05A: "shellder",
    0x05B: "cloyster",
    0x05C: "gastly",
    0x05D: "haunter",
    0x05E: "gengar",
    0x05F: "onix",
    0x060: "drowzee",
    0x061: "hypno",
    0x062: "krabby",
    0x063: "kingler",
    0x064: "voltorb",
    0x065: "electrode",
    0x066: "exeggcute",
    0x067: "exeggutor",
    0x068: "cubone",
    0x069: "marowak",
    0x06A: "hitmonlee",
    0x06B: "hitmonchan",
    0x06C: "lickitung",
    0x06D: "koffing",
    0x06E: "weezing",
    0x06F: "rhyhorn",
    0x070: "rhydon",
    0x071: "chansey",
    0x072: "tangela",
    0x073: "kangaskhan",
    0x074: "horsea",
    0x075: "seadra",
    0x076: "goldeen",
    0x077: "seaking",
    0x078: "staryu",
    0x079: "starmie",
    0x07A: "mr-mime",
    0x07B: "scyther",
    0x07C: "jynx",
    0x07D: "electabuzz",
    0x07E: "magmar",
    0x07F: "pinsir",
    0x080: "tauros",
    0x081: "magikarp",
    0x082: "gyarados",
    0x083: "lapras",
    0x084: "ditto",
    0x085: "eevee",
    0x086: "vaporeon",
    0x087: "jolteon",
    0x088: "flareon",
    0x089: "porygon",
    0x08A: "omanyte",
    0x08B: "omastar",
    0x08C: "kabuto",
    0x08D: "kabutops",
    0x08E: "aerodactyl",
    0x08F: "snorlax",
    0x090: "articuno",
    0x091: "zapdos",
    0x092: "moltres",
    0x093: "dratini",
    0x094: "dragonair",
    0x095: "dragonite",
    0x096: "mewtwo",
    0x097: "mew",
    0x098: "chikorita",
    0x099: "bayleef",
    0x09A: "meganium",
    0x09B: "cyndaquil",
    0x09C: "quilava",
    0x09D: "typhlosion",
    0x09E: "totodile",
    0x09F: "croconaw",
    0x0A0: "feraligatr",
    0x0A1: "sentret",
    0x0A2: "furret",
    0x0A3: "hoothoot",
    0x0A4: "noctowl",
    0x0A5: "ledyba",
    0x0A6: "ledian",
    0x0A7: "spinarak",
    0x0A8: "ariados",
    0x0A9: "crobat",
    0x0AA: "chinchou",
    0x0AB: "lanturn",
    0x0AC: "pichu",
    0x0AD: "cleffa",
    0x0AE: "igglybuff",
    0x0AF: "togepi",
    0x0B0: "togetic",
    0x0B1: "natu",
    0x0B2: "xatu",
    0x0B3: "mareep",
    0x0B4: "flaaffy",
    0x0B5: "ampharos",
    0x0B6: "bellossom",
    0x0B7: "marill",
    0x0B8: "azumarill",
    0x0B9: "sudowoodo",
    0x0BA: "politoed",
    0x0BB: "hoppip",
    0x0BC: "skiploom",
    0x0BD: "jumpluff",
    0x0BE: "aipom",
    0x0BF: "sunkern",
    0x0C0: "sunflora",
    0x0C1: "yanma",
    0x0C2: "wooper",
    0x0C3: "quagsire",
    0x0C4: "espeon",
    0x0C5: "umbreon",
    0x0C6: "murkrow",
    0x0C7: "slowking",
    0x0C8: "misdreavus",
    0x0C9: "unown",
    0x0CA: "wobbuffet",
    0x0CB: "girafarig",
    0x0CC: "pineco",
    0x0CD: "forretress",
    0x0CE: "dunsparce",
    0x0CF: "gligar",
    0x0D0: "steelix",
    0x0D1: "snubbull",
    0x0D2: "granbull",
    0x0D3: "qwilfish",
    0x0D4: "scizor",
    0x0D5: "shuckle",
    0x0D6: "heracross",
    0x0D7: "sneasel",
    0x0D8: "teddiursa",
    0x0D9: "ursaring",
    0x0DA: "slugma",
    0x0DB: "magcargo",
    0x0DC: "swinub",
    0x0DD: "piloswine",
    0x0DE: "corsola",
    0x0DF: "remoraid",
    0x0E0: "octillery",
    0x0E1: "delibird",
    0x0E2: "mantine",
    0x0E3: "skarmory",
    0x0E4: "houndour",
    0x0E5: "houndoom",
    0x0E6: "kingdra",
    0x0E7: "phanpy",
    0x0E8: "donphan",
    0x0E9: "porygon2",
    0x0EA: "stantler",
    0x0EB: "smeargle",
    0x0EC: "tyrogue",
    0x0ED: "hitmontop",
    0x0EE: "smoochum",
    0x0EF: "elekid",
    0x0F0: "magby",
    0x0F1: "miltank",
    0x0F2: "blissey",
    0x0F3: "raikou",
    0x0F4: "entei",
    0x0F5: "suicune",
    0x0F6: "larvitar",
    0x0F7: "pupitar",
    0x0F8: "tyranitar",
    0x0F9: "lugia",
    0x0FA: "ho-oh",
    0x0FB: "celebi",
    0x115: "treecko",
    0x116: "grovyle",
    0x117: "sceptile",
    0x118: "torchic",
    0x119: "combusken",
    0x11A: "blaziken",
    0x11B: "mudkip",
    0x11C: "marshtomp",
    0x11D: "swampert",
    0x11E: "poochyena",
    0x11F: "mightyena",
    0x120: "zigzagoon",
    0x121: "linoone",
    0x122: "wurmple",
    0x123: "silcoon",
    0x124: "beautifly",
    0x125: "cascoon",
    0x126: "dustox",
    0x127: "lotad",
    0x128: "lombre",
    0x129: "ludicolo",
    0x12A: "seedot",
    0x12B: "nuzleaf",
    0x12C: "shiftry",
    0x12D: "nincada",
    0x12E: "ninjask",
    0x12F: "shedinja",
    0x130: "taillow",
    0x131: "swellow",
    0x132: "shroomish",
    0x133: "breloom",
    0x134: "spinda",
    0x135: "wingull",
    0x136: "pelipper",
    0x137: "surskit",
    0x138: "masquerain",
    0x139: "wailmer",
    0x13A: "wailord",
    0x13B: "skitty",
    0x13C: "delcatty",
    0x13D: "kecleon",
    0x13E: "baltoy",
    0x13F: "claydol",
    0x140: "nosepass",
    0x141: "torkoal",
    0x142: "sableye",
    0x143: "barboach",
    0x144: "whiscash",
    0x145: "luvdisc",
    0x146: "corphish",
    0x147: "crawdaunt",
    0x148: "feebas",
    0x149: "milotic",
    0x14A: "carvanha",
    0x14B: "sharpedo",
    0x14C: "trapinch",
    0x14D: "vibrava",
    0x14E: "flygon",
    0x14F: "makuhita",
    0x150: "hariyama",
    0x151: "electrike",
    0x152: "manectric",
    0x153: "numel",
    0x154: "camerupt",
    0x155: "spheal",
    0x156: "sealeo",
    0x157: "walrein",
    0x158: "cacnea",
    0x159: "cacturne",
    0x15A: "snorunt",
    0x15B: "glalie",
    0x15C: "lunatone",
    0x15D: "solrock",
    0x15E: "azurill",
    0x15F: "spoink",
    0x160: "grumpig",
    0x161: "plusle",
    0x162: "minun",
    0x163: "mawile",
    0x164: "meditite",
    0x165: "medicham",
    0x166: "swablu",
    0x167: "altaria",
    0x168: "wynaut",
    0x169: "duskull",
    0x16A: "dusclops",
    0x16B: "roselia",
    0x16C: "slakoth",
    0x16D: "vigoroth",
    0x16E: "slaking",
    0x16F: "gulpin",
    0x170: "swalot",
    0x171: "tropius",
    0x172: "whismur",
    0x173: "loudred",
    0x174: "exploud",
    0x175: "clamperl",
    0x176: "huntail",
    0x177: "gorebyss",
    0x178: "absol",
    0x179: "shuppet",
    0x17A: "banette",
    0x17B: "seviper",
    0x17C: "zangoose",
    0x17D: "relicanth",
    0x17E: "aron",
    0x17F: "lairon",
    0x180: "aggron",
    0x181: "castform",
    0x182: "volbeat",
    0x183: "illumise",
    0x184: "lileep",
    0x185: "cradily",
    0x186: "anorith",
    0x187: "armaldo",
    0x188: "ralts",
    0x189: "kirlia",
    0x18A: "gardevoir",
    0x18B: "bagon",
    0x18C: "shelgon",
    0x18D: "salamence",
    0x18E: "beldum",
    0x18F: "metang",
    0x190: "metagross",
    0x191: "regirock",
    0x192: "regice",
    0x193: "registeel",
    0x194: "kyogre",
    0x195: "groudon",
    0x196: "rayquaza",
    0x197: "latias",
    0x198: "latios",
    0x199: "jirachi",
    0x19A: "deoxys",
    0x19B: "chimecho",
}
