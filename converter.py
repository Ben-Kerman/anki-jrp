import os.path
from typing import List, Tuple

from accent_dict import AccentDict
from mecab import Mecab, MecabUnit
from normalize import is_hiragana, to_hiragana

_mecab_inst: Mecab | None = None
_acc_dict: AccentDict | None = None


def _get_mecab_inst() -> Mecab:
    global _mecab_inst

    if _mecab_inst is None:
        _mecab_inst = Mecab()
    return _mecab_inst


def _get_acc_dict() -> AccentDict:
    global _acc_dict

    if _acc_dict is None:
        _acc_dict = AccentDict(os.path.join(os.path.dirname(__file__), "acc_dict.xz"))
    return _acc_dict


class Segment:
    text: str
    reading: str | None

    def __init__(self, text: str, reading: str | None = None):
        self.text = text
        self.reading = reading

    def __repr__(self):
        return f"S[{self.text},{self.reading}]"


class Unit:
    segments: list[Segment]
    accents: list[int]
    base_form: Segment | None

    def __init__(self, segments: list[Segment],
                 accents: list[int] | None = None,
                 base_form: Segment | None = None):
        self.segments = segments
        if accents is None:
            self.accents = []
        else:
            self.accents = accents
        self.base_form = base_form

    def __repr__(self):
        return f"U[{self.segments},{self.accents},{self.base_form}]"


def _handle_josi(munit: MecabUnit) -> Unit:
    if to_hiragana(munit.orig) == to_hiragana(munit.reading):
        return Unit([Segment(munit.orig)])
    else:
        return Unit([Segment(munit.orig, to_hiragana(munit.reading))])


def _handle_yougen(acc_dict: AccentDict, munits: list[MecabUnit], idx: int) -> tuple[int, Unit]:
    def gen_mecab_reading(unit: MecabUnit) -> str:
        if is_hiragana(unit.base_form):
            return unit.base_form

        itr = enumerate(zip(reversed(unit.orig), reversed(unit.reading)))
        for i, (co, cr) in itr:
            if co != cr:
                break

        # TODO: handle undefined i
        return unit.reading[0:len(unit.reading) - i] + unit.base_form[len(unit.orig) - i:]

    mu = munits[idx]
    mecab_reading: str = gen_mecab_reading(mu)

    return idx + 1, Unit([Segment(mu.orig, mecab_reading)])


def _handle_other(acc_dict: AccentDict, munits: list[MecabUnit], idx: int) -> tuple[int, Unit]:
    munit = munits[idx]
    return idx + 1, Unit([Segment(munit.orig, munit.reading)])


def convert(txt: str,
            mecab: Mecab = None,
            acc_dict: AccentDict = None) -> list[Unit]:
    if mecab is None:
        mecab = _get_mecab_inst()
    if acc_dict is None:
        acc_dict = _get_acc_dict()

    munits = mecab.analyze(txt)
    units: list[Unit] = []
    i = 0
    while i < len(munits):
        match munits[i].hinsi:
            case "助詞" | "助動詞":
                unit = _handle_josi(munits[i])
                i += 1
            case "動詞" | "形容詞":
                i, unit = _handle_yougen(acc_dict, munits, i)
            case "記号":
                unit = Unit([Segment(munits[i].orig)])
                i += 1
            case _:
                i, unit = _handle_other(acc_dict, munits, i)
        units.append(unit)
    return units
