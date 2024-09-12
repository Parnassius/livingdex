from __future__ import annotations

import struct
from pathlib import Path


def parse(save: Path, sub_parser: str) -> list[list[str]]:
    assert sub_parser == ""

    boxes = []
    with save.open("rb") as f:
        for box_index in range(24):
            f.seek(0x400 + box_index * 0x1000)
            box = []
            for _ in range(30):
                pid, flags, checksum, *data = struct.unpack("<LHH64H", f.read(0x88))
                key = checksum
                for i in range(len(data)):
                    key = (0x41C64E6D * key) + 0x00006073
                    data[i] = data[i] ^ ((key >> 16) & 0xFFFF)

                if (
                    pid == 0
                    and flags == 0
                    and checksum == 0
                    and all(x == 0 for x in data)
                ):
                    pokemon = ""
                else:
                    sections = _sections_positions[((pid >> 13) & 0x1F) % 24]
                    is_egg = (data[sections[1] * 16 + 9] >> 14) & 1
                    if is_egg:
                        pokemon = "egg"
                    else:
                        pokemon_info = _indices[data[sections[0] * 16] & 0xFFFF]
                        if isinstance(pokemon_info, tuple):
                            form = pokemon_info[1][
                                (data[sections[1] * 16 + 12] & 0xFF) >> 3
                            ]
                            pokemon = pokemon_info[0]
                            if form:
                                pokemon += f"-{form}"
                        else:
                            pokemon = pokemon_info
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

_indices: dict[int, str | tuple[str, list[str]]] = {
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
    0x0C9: ("unown", [*"abcdefghijklmnopqrstuvwxyz", "exclamation", "question"]),
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
    0x0FC: "treecko",
    0x0FD: "grovyle",
    0x0FE: "sceptile",
    0x0FF: "torchic",
    0x100: "combusken",
    0x101: "blaziken",
    0x102: "mudkip",
    0x103: "marshtomp",
    0x104: "swampert",
    0x105: "poochyena",
    0x106: "mightyena",
    0x107: "zigzagoon",
    0x108: "linoone",
    0x109: "wurmple",
    0x10A: "silcoon",
    0x10B: "beautifly",
    0x10C: "cascoon",
    0x10D: "dustox",
    0x10E: "lotad",
    0x10F: "lombre",
    0x110: "ludicolo",
    0x111: "seedot",
    0x112: "nuzleaf",
    0x113: "shiftry",
    0x114: "taillow",
    0x115: "swellow",
    0x116: "wingull",
    0x117: "pelipper",
    0x118: "ralts",
    0x119: "kirlia",
    0x11A: "gardevoir",
    0x11B: "surskit",
    0x11C: "masquerain",
    0x11D: "shroomish",
    0x11E: "breloom",
    0x11F: "slakoth",
    0x120: "vigoroth",
    0x121: "slaking",
    0x122: "nincada",
    0x123: "ninjask",
    0x124: "shedinja",
    0x125: "whismur",
    0x126: "loudred",
    0x127: "exploud",
    0x128: "makuhita",
    0x129: "hariyama",
    0x12A: "azurill",
    0x12B: "nosepass",
    0x12C: "skitty",
    0x12D: "delcatty",
    0x12E: "sableye",
    0x12F: "mawile",
    0x130: "aron",
    0x131: "lairon",
    0x132: "aggron",
    0x133: "meditite",
    0x134: "medicham",
    0x135: "electrike",
    0x136: "manectric",
    0x137: "plusle",
    0x138: "minun",
    0x139: "volbeat",
    0x13A: "illumise",
    0x13B: "roselia",
    0x13C: "gulpin",
    0x13D: "swalot",
    0x13E: "carvanha",
    0x13F: "sharpedo",
    0x140: "wailmer",
    0x141: "wailord",
    0x142: "numel",
    0x143: "camerupt",
    0x144: "torkoal",
    0x145: "spoink",
    0x146: "grumpig",
    0x147: "spinda",
    0x148: "trapinch",
    0x149: "vibrava",
    0x14A: "flygon",
    0x14B: "cacnea",
    0x14C: "cacturne",
    0x14D: "swablu",
    0x14E: "altaria",
    0x14F: "zangoose",
    0x150: "seviper",
    0x151: "lunatone",
    0x152: "solrock",
    0x153: "barboach",
    0x154: "whiscash",
    0x155: "corphish",
    0x156: "crawdaunt",
    0x157: "baltoy",
    0x158: "claydol",
    0x159: "lileep",
    0x15A: "cradily",
    0x15B: "anorith",
    0x15C: "armaldo",
    0x15D: "feebas",
    0x15E: "milotic",
    0x15F: "castform",
    0x160: "kecleon",
    0x161: "shuppet",
    0x162: "banette",
    0x163: "duskull",
    0x164: "dusclops",
    0x165: "tropius",
    0x166: "chimecho",
    0x167: "absol",
    0x168: "wynaut",
    0x169: "snorunt",
    0x16A: "glalie",
    0x16B: "spheal",
    0x16C: "sealeo",
    0x16D: "walrein",
    0x16E: "clamperl",
    0x16F: "huntail",
    0x170: "gorebyss",
    0x171: "relicanth",
    0x172: "luvdisc",
    0x173: "bagon",
    0x174: "shelgon",
    0x175: "salamence",
    0x176: "beldum",
    0x177: "metang",
    0x178: "metagross",
    0x179: "regirock",
    0x17A: "regice",
    0x17B: "registeel",
    0x17C: "latias",
    0x17D: "latios",
    0x17E: "kyogre",
    0x17F: "groudon",
    0x180: "rayquaza",
    0x181: "jirachi",
    0x182: ("deoxys", ["normal", "attack", "defense", "speed"]),
    0x183: "turtwig",
    0x184: "grotle",
    0x185: "torterra",
    0x186: "chimchar",
    0x187: "monferno",
    0x188: "infernape",
    0x189: "piplup",
    0x18A: "prinplup",
    0x18B: "empoleon",
    0x18C: "starly",
    0x18D: "staravia",
    0x18E: "staraptor",
    0x18F: "bidoof",
    0x190: "bibarel",
    0x191: "kricketot",
    0x192: "kricketune",
    0x193: "shinx",
    0x194: "luxio",
    0x195: "luxray",
    0x196: "budew",
    0x197: "roserade",
    0x198: "cranidos",
    0x199: "rampardos",
    0x19A: "shieldon",
    0x19B: "bastiodon",
    0x19C: ("burmy", ["plant", "sandy", "trash"]),
    0x19D: ("wormadam", ["plant", "sandy", "trash"]),
    0x19E: "mothim",
    0x19F: "combee",
    0x1A0: "vespiquen",
    0x1A1: "pachirisu",
    0x1A2: "buizel",
    0x1A3: "floatzel",
    0x1A4: "cherubi",
    0x1A5: "cherrim",
    0x1A6: ("shellos", ["west", "east"]),
    0x1A7: ("gastrodon", ["west", "east"]),
    0x1A8: "ambipom",
    0x1A9: "drifloon",
    0x1AA: "drifblim",
    0x1AB: "buneary",
    0x1AC: "lopunny",
    0x1AD: "mismagius",
    0x1AE: "honchkrow",
    0x1AF: "glameow",
    0x1B0: "purugly",
    0x1B1: "chingling",
    0x1B2: "stunky",
    0x1B3: "skuntank",
    0x1B4: "bronzor",
    0x1B5: "bronzong",
    0x1B6: "bonsly",
    0x1B7: "mime-jr",
    0x1B8: "happiny",
    0x1B9: "chatot",
    0x1BA: "spiritomb",
    0x1BB: "gible",
    0x1BC: "gabite",
    0x1BD: "garchomp",
    0x1BE: "munchlax",
    0x1BF: "riolu",
    0x1C0: "lucario",
    0x1C1: "hippopotas",
    0x1C2: "hippowdon",
    0x1C3: "skorupi",
    0x1C4: "drapion",
    0x1C5: "croagunk",
    0x1C6: "toxicroak",
    0x1C7: "carnivine",
    0x1C8: "finneon",
    0x1C9: "lumineon",
    0x1CA: "mantyke",
    0x1CB: "snover",
    0x1CC: "abomasnow",
    0x1CD: "weavile",
    0x1CE: "magnezone",
    0x1CF: "lickilicky",
    0x1D0: "rhyperior",
    0x1D1: "tangrowth",
    0x1D2: "electivire",
    0x1D3: "magmortar",
    0x1D4: "togekiss",
    0x1D5: "yanmega",
    0x1D6: "leafeon",
    0x1D7: "glaceon",
    0x1D8: "gliscor",
    0x1D9: "mamoswine",
    0x1DA: "porygon-z",
    0x1DB: "gallade",
    0x1DC: "probopass",
    0x1DD: "dusknoir",
    0x1DE: "froslass",
    0x1DF: ("rotom", ["", "heat", "wash", "frost", "fan", "mow"]),
    0x1E0: "uxie",
    0x1E1: "mesprit",
    0x1E2: "azelf",
    0x1E3: "dialga",
    0x1E4: "palkia",
    0x1E5: "heatran",
    0x1E6: "regigigas",
    0x1E7: ("giratina", ["altered", "origin"]),
    0x1E8: "cresselia",
    0x1E9: "phione",
    0x1EA: "manaphy",
    0x1EB: "darkrai",
    0x1EC: "shaymin",
    0x1ED: "arceus",
    0x1EE: "victini",
    0x1EF: "snivy",
    0x1F0: "servine",
    0x1F1: "serperior",
    0x1F2: "tepig",
    0x1F3: "pignite",
    0x1F4: "emboar",
    0x1F5: "oshawott",
    0x1F6: "dewott",
    0x1F7: "samurott",
    0x1F8: "patrat",
    0x1F9: "watchog",
    0x1FA: "lillipup",
    0x1FB: "herdier",
    0x1FC: "stoutland",
    0x1FD: "purrloin",
    0x1FE: "liepard",
    0x1FF: "pansage",
    0x200: "simisage",
    0x201: "pansear",
    0x202: "simisear",
    0x203: "panpour",
    0x204: "simipour",
    0x205: "munna",
    0x206: "musharna",
    0x207: "pidove",
    0x208: "tranquill",
    0x209: "unfezant",
    0x20A: "blitzle",
    0x20B: "zebstrika",
    0x20C: "roggenrola",
    0x20D: "boldore",
    0x20E: "gigalith",
    0x20F: "woobat",
    0x210: "swoobat",
    0x211: "drilbur",
    0x212: "excadrill",
    0x213: "audino",
    0x214: "timburr",
    0x215: "gurdurr",
    0x216: "conkeldurr",
    0x217: "tympole",
    0x218: "palpitoad",
    0x219: "seismitoad",
    0x21A: "throh",
    0x21B: "sawk",
    0x21C: "sewaddle",
    0x21D: "swadloon",
    0x21E: "leavanny",
    0x21F: "venipede",
    0x220: "whirlipede",
    0x221: "scolipede",
    0x222: "cottonee",
    0x223: "whimsicott",
    0x224: "petilil",
    0x225: "lilligant",
    0x226: ("basculin", ["red-striped", "blue-striped"]),
    0x227: "sandile",
    0x228: "krokorok",
    0x229: "krookodile",
    0x22A: "darumaka",
    0x22B: "darmanitan",
    0x22C: "maractus",
    0x22D: "dwebble",
    0x22E: "crustle",
    0x22F: "scraggy",
    0x230: "scrafty",
    0x231: "sigilyph",
    0x232: "yamask",
    0x233: "cofagrigus",
    0x234: "tirtouga",
    0x235: "carracosta",
    0x236: "archen",
    0x237: "archeops",
    0x238: "trubbish",
    0x239: "garbodor",
    0x23A: "zorua",
    0x23B: "zoroark",
    0x23C: "minccino",
    0x23D: "cinccino",
    0x23E: "gothita",
    0x23F: "gothorita",
    0x240: "gothitelle",
    0x241: "solosis",
    0x242: "duosion",
    0x243: "reuniclus",
    0x244: "ducklett",
    0x245: "swanna",
    0x246: "vanillite",
    0x247: "vanillish",
    0x248: "vanilluxe",
    0x249: ("deerling", ["spring", "summer", "autumn", "winter"]),
    0x24A: ("sawsbuck", ["spring", "summer", "autumn", "winter"]),
    0x24B: "emolga",
    0x24C: "karrablast",
    0x24D: "escavalier",
    0x24E: "foongus",
    0x24F: "amoonguss",
    0x250: "frillish",
    0x251: "jellicent",
    0x252: "alomomola",
    0x253: "joltik",
    0x254: "galvantula",
    0x255: "ferroseed",
    0x256: "ferrothorn",
    0x257: "klink",
    0x258: "klang",
    0x259: "klinklang",
    0x25A: "tynamo",
    0x25B: "eelektrik",
    0x25C: "eelektross",
    0x25D: "elgyem",
    0x25E: "beheeyem",
    0x25F: "litwick",
    0x260: "lampent",
    0x261: "chandelure",
    0x262: "axew",
    0x263: "fraxure",
    0x264: "haxorus",
    0x265: "cubchoo",
    0x266: "beartic",
    0x267: "cryogonal",
    0x268: "shelmet",
    0x269: "accelgor",
    0x26A: "stunfisk",
    0x26B: "mienfoo",
    0x26C: "mienshao",
    0x26D: "druddigon",
    0x26E: "golett",
    0x26F: "golurk",
    0x270: "pawniard",
    0x271: "bisharp",
    0x272: "bouffalant",
    0x273: "rufflet",
    0x274: "braviary",
    0x275: "vullaby",
    0x276: "mandibuzz",
    0x277: "heatmor",
    0x278: "durant",
    0x279: "deino",
    0x27A: "zweilous",
    0x27B: "hydreigon",
    0x27C: "larvesta",
    0x27D: "volcarona",
    0x27E: "cobalion",
    0x27F: "terrakion",
    0x280: "virizion",
    0x281: ("tornadus", ["incarnate", "therian"]),
    0x282: ("thundurus", ["incarnate", "therian"]),
    0x283: "reshiram",
    0x284: "zekrom",
    0x285: ("landorus", ["incarnate", "therian"]),
    0x286: ("kyurem", ["", "white", "black"]),
    0x287: ("keldeo", ["ordinary", "resolute"]),
    0x288: "meloetta",
    0x289: ("genesect", ["", "douse", "shock", "burn", "chill"]),
}