from livingdex.pkhex.core import PKHeX


def test_pkhex() -> None:
    assert int(PKHeX.Core.Species.Pikachu) == 25
