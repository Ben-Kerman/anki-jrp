from dictionary import Dictionary
from mecab import Mecab, MecabUnit
from normalize import is_kana, to_hiragana


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


def _handle_josi(munit: MecabUnit) -> Unit:
    if to_hiragana(munit.value) == to_hiragana(munit.reading):
        return Unit([Segment(munit.value)])
    else:
        return Unit([Segment(munit.value, to_hiragana(munit.reading))])


def _handle_yougen(dic: Dictionary, munits: list[MecabUnit], idx: int) -> tuple[int, Unit]:
    def gen_mecab_reading(unit: MecabUnit) -> str:
        if is_kana(unit.base_form):
            return unit.base_form

        itr = enumerate(zip(reversed(unit.value), reversed(unit.reading)))
        for i, (co, cr) in itr:
            if co != cr:
                break

        # TODO: handle undefined i
        return unit.reading[0:len(unit.reading) - i] + unit.base_form[len(unit.value) - i:]

    mu = munits[idx]
    mecab_reading: str = gen_mecab_reading(mu)

    return idx + 1, Unit([Segment(mu.value, mecab_reading)])


def _handle_other(dic: Dictionary, munits: list[MecabUnit], idx: int) -> tuple[int, Unit]:
    munit = munits[idx]
    return idx + 1, Unit([Segment(munit.value, munit.reading)])


def convert(txt: str, mecab: Mecab, dic: Dictionary) -> list[Unit]:
    munits = mecab.analyze(txt)
    units: list[Unit] = []
    i = 0
    while i < len(munits):
        match munits[i].hinsi:
            case "助詞" | "助動詞":
                unit = _handle_josi(munits[i])
                i += 1
            case "動詞" | "形容詞":
                i, unit = _handle_yougen(dic, munits, i)
            case "記号":
                unit = Unit([Segment(munits[i].value)])
                i += 1
            case _:
                i, unit = _handle_other(dic, munits, i)
        units.append(unit)
    return units
