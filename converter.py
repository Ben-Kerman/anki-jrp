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
    last_idx: int
    hinsi_type: HinsiType
    word: str
    base_word: str | None
    lookup: Lookup


def _dsc(_) -> bool:
    return False


def find_longest_match(dic: Dictionary, idx: int, punits: list[ParserUnit],
                       prefer_accent: bool = False,
                       stop_cond: Callable[[MecabUnit], bool] = _dsc) -> Match | None:
    acc_match: Match | None = None
    plain_match: Match | None = None
    for i in range(idx, len(punits)):
        pu = punits[i]
        if not isinstance(pu, MecabUnit) or stop_cond(pu):
            break

        hinsi = pu.hinsi_type()
        reading_guess = "".join(map(lambda u: u.reading, punits[idx:i]))
        reading_guess += pu.reading if hinsi != HinsiType.YOUGEN else _yougen_base_reading(pu)
        part_word = "".join(map(lambda u: u.value, punits[idx:i]))
        word = part_word + pu.value
        base_word = part_word + pu.value if hinsi == HinsiType.YOUGEN else None

        lu = dic.look_up(base_word or word, reading_guess)
        if lu:
            match = Match(i, hinsi, word, base_word, lu)
            if lu.has_accents():
                acc_match = match
            else:
                plain_match = match
    if acc_match:
        if prefer_accent:
            return acc_match
        elif plain_match and plain_match.last_idx > acc_match.last_idx:
            return plain_match
        else:
            return acc_match
    else:
        return plain_match


def _handle_josi(munit: MecabUnit) -> Unit:
    if to_hiragana(munit.value) == to_hiragana(munit.reading):
        return Unit([Segment(munit.value)])
    else:
        return Unit([Segment(munit.value, to_hiragana(munit.reading))])


def _handle_yougen(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit]:
    mu = cast(MecabUnit, punits[idx])
    mecab_reading: str = _yougen_base_reading(mu)

    return idx + 1, Unit([Segment(mu.value, mecab_reading)])


def _handle_other(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit]:
    m = find_longest_match(dic, idx, punits, p.prefer_accent_lookups, lambda u: u.hinsi_type() == HinsiType.ZYOSI)
    if m:
        res = m.lookup.results[0]
        return m.last_idx + 1, Unit([Segment(m.word, res.reading)], res.accents)
    else:
        mu = cast(MecabUnit, punits[idx])
        return idx + 1, Unit([Segment(mu.value, mu.reading)])


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
                    i, unit = _handle_other(prefs, dic, punits, i)
        else:
            unit = Unit([Segment(pu.value)])
        units.append(unit)
    return units
