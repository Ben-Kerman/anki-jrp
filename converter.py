from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from dictionary import Dictionary, Lookup
from mecab import HinsiType, Mecab, MecabUnit, ParserUnit
from normalize import is_kana, to_hiragana
from preferences import ConvPrefs


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
        self.accents = accents or []
        self.base_form = base_form

    def __repr__(self):
        return f"U[{self.segments},{self.accents},{self.base_form}]"


def _yougen_base_reading(unit: MecabUnit) -> str:
    if is_kana(unit.base_form):
        return unit.base_form

    itr = enumerate(zip(reversed(unit.value), reversed(unit.reading)))
    for i, (co, cr) in itr:
        if co != cr:
            break

    # TODO: handle undefined i
    return unit.reading[0:len(unit.reading) - i] + unit.base_form[len(unit.value) - i:]


@dataclass
class Match:
    next_idx: int
    hinsi_type: HinsiType
    lookup: Lookup


def _dsc(_) -> bool:
    return False


def find_longest_match(dic: Dictionary, idx: int, punits: list[ParserUnit],
                       stop_cond: Callable[[MecabUnit], bool] = _dsc) -> tuple[Match | None, Match | None]:
    has_accent: Match | None = None
    no_accent: Match | None = None
    for i in range(idx, len(punits)):
        pu = punits[i]
        if not isinstance(pu, MecabUnit) or stop_cond(pu):
            break

        reading_guess = "".join(map(lambda u: u.reading, punits[idx:i]))
        reading_guess += pu.reading if pu.hinsi_type() != HinsiType.YOUGEN else _yougen_base_reading(pu)
        word = "".join(map(lambda u: u.value, punits[idx:i]))
        word += pu.value if pu.hinsi_type() != HinsiType.YOUGEN else pu.base_form

        lu = dic.look_up(word, reading_guess)
        if lu:
            match = Match(i + 1, pu.hinsi_type(), lu)
            if lu.has_accents():
                has_accent = match
            else:
                no_accent = match
    return has_accent, no_accent


def _handle_josi(munit: MecabUnit) -> Unit:
    if to_hiragana(munit.value) == to_hiragana(munit.reading):
        return Unit([Segment(munit.value)])
    else:
        return Unit([Segment(munit.value, to_hiragana(munit.reading))])


def _handle_yougen(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit]:
    mu = cast(MecabUnit, punits[idx])
    mecab_reading: str = _yougen_base_reading(mu)

    return idx + 1, Unit([Segment(mu.value, mecab_reading)])


def _handle_other(dic: Dictionary, munits: list[ParserUnit], idx: int) -> tuple[int, Unit]:
    munit = cast(MecabUnit, munits[idx])
    return idx + 1, Unit([Segment(munit.value, munit.reading)])


def convert(txt: str, prefs: ConvPrefs, mecab: Mecab, dic: Dictionary) -> list[Unit]:
    punits = mecab.analyze(txt)
    units: list[Unit] = []
    i = 0
    while i < len(punits):
        pu = punits[i]
        if isinstance(pu, MecabUnit):
            match pu.hinsi_type():
                case HinsiType.ZYOSI:
                    unit = _handle_josi(pu)
                    i += 1
                case HinsiType.YOUGEN:
                    i, unit = _handle_yougen(prefs, dic, punits, i)
                case HinsiType.SYMBOL:
                    unit = Unit([Segment(pu.value)])
                    i += 1
                case _:
                    i, unit = _handle_other(dic, punits, i)
        else:
            unit = Unit([Segment(pu.value)])
        units.append(unit)
    return units
