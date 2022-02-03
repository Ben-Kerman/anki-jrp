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
    base_form: str | None

    def __init__(self, segments: list[Segment],
                 accents: list[int] | None = None,
                 base_form: str | None = None):
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
        if all(isinstance(u, MecabUnit) and u.hinsi != "未知語" for u in punits[idx:i + 1]):
            reading_guess = "".join(map(lambda u: u.reading, punits[idx:i]))
            reading_guess += pu.reading if hinsi != HinsiType.YOUGEN else _yougen_base_reading(pu)
        else:
            reading_guess = None
        part_word = "".join(map(lambda u: u.value, punits[idx:i]))
        word = part_word + pu.value
        base_word = part_word + pu.base_form if hinsi == HinsiType.YOUGEN else None

        lu = dic.look_up(base_word or word, reading_guess)
        if lu:
            match = Match(i, word, base_word, lu)
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


def _yougen_join(p: ConvPrefs, punits: list[ParserUnit], bmu: MecabUnit,
                 idx: int, prev: str = "") -> tuple[int, str, Unit | None]:
    if idx >= len(punits) or not isinstance(punits[idx], MecabUnit):
        return idx, prev, None
    mu = cast(MecabUnit, punits[idx])

    if p.yougen_join_nai:
        for_dousi = bmu.hinsi == "動詞" and bmu.conj_form == "未然形"
        for_keiyousi = bmu.hinsi == "形容詞" and bmu.conj_form == "連用テ接続"
        for_tai = bmu.conj_type == "特殊・タイ" and bmu.conj_form == "連用テ接続"
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "特殊・ナイ"
        if any((for_dousi, for_keiyousi, for_tai)) and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.yougen_join_u:
        for_base = bmu.hinsi in ("動詞", "形容詞", "助動詞") and bmu.conj_form == "未然ウ接続"
        for_cur = mu.hinsi == "助動詞" and mu.base_form == "う"
        if for_base and for_cur:
            return idx + 1, prev + mu.value, None
    if p.yougen_join_ta:
        for_dousi = bmu.hinsi == "動詞" and bmu.conj_form in ("連用形", "連用タ接続")
        for_keiyousi = bmu.hinsi == "形容詞" and bmu.conj_form == "連用タ接続"
        for_zyosi = bmu.hinsi == "助動詞" and bmu.conj_form in ("連用形", "連用タ接続")
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "特殊・タ"
        if any((for_dousi, for_keiyousi, for_zyosi)) and for_cur:
            return idx + 1, prev + mu.value, None
    if p.yougen_join_te:
        for_dousi = bmu.hinsi == "動詞" and bmu.conj_form in ("連用形", "連用タ接続")
        for_keiyousi = bmu.hinsi == "形容詞" and bmu.conj_form == "連用テ接続"
        for_zyosi = bmu.hinsi == "助動詞" and bmu.conj_form in ("連用形", "連用テ接続")
        for_cur = mu.comp_hinsi("助詞", "接続助詞") and mu.base_form in ("て", "で")
        if any((for_dousi, for_keiyousi, for_zyosi)) and for_cur:
            return idx + 1, prev + mu.value, None
    if p.yougen_join_ba:
        for_base = bmu.hinsi in ("動詞", "形容詞", "助動詞")
        for_cur = mu.comp_hinsi("助詞", "接続助詞") and mu.base_form == "ば"
        if for_base and for_cur:
            return idx + 1, prev + mu.value, None
    if p.yougen_join_sou:
        for_dousi = bmu.hinsi == "動詞" and bmu.conj_form == "連用形"
        for_keiyousi = bmu.hinsi == "形容詞" and bmu.conj_form == "ガル接続"
        for_zyosi = bmu.conj_type in ("特殊・タイ", "特殊・ナイ") and bmu.conj_form == "ガル接続"
        for_sa = bmu.comp_hinsi("名詞", "接尾", "特殊") and bmu.base_form == "さ"
        for_cur = mu.comp_hinsi("名詞", "接尾", "助動詞語幹") and mu.base_form == "そう"
        if any((for_dousi, for_keiyousi, for_zyosi, for_sa)) and for_cur:
            return idx + 1, prev + mu.value, None

    if p.keiyousi_join_sa:
        for_keiyousi = bmu.hinsi == "形容詞" and bmu.conj_form == "ガル接続"
        for_zyosi = bmu.conj_type in ("特殊・タイ", "特殊・ナイ") and bmu.conj_form == "ガル接続"
        for_cur = mu.comp_hinsi("名詞", "接尾", "特殊") and mu.base_form == "さ"
        if for_keiyousi or for_zyosi and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)

    if p.dousi_join_tai:
        for_base = bmu.hinsi == "動詞" and bmu.conj_form == "連用形"
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "特殊・タイ"
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_join_nu:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form == "未然形"
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "特殊・ヌ"
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_join_n:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form == "未然形"
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "不変化型" and mu.base_form == "ん"
        if for_base and for_cur:
            return idx + 1, prev + mu.value, None
    if p.dousi_join_reru:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form in ("未然形", "未然レル接続")
        for_cur = mu.comp_hinsi("動詞", "接尾") and mu.base_form in ("れる", "られる")
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_join_seru:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form in ("未然形", "未然レル接続")
        for_cur = mu.comp_hinsi("動詞", "接尾") and mu.base_form in ("せる", "させる")
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_join_masu:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form == "連用形"
        for_cur = mu.hinsi == "助動詞" and mu.conj_type == "特殊・マス"
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_join_tyau:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form in ("連用形", "連用タ接続")
        for_cur = mu.comp_hinsi("動詞", "非自立") and mu.base_form == "ちゃう"
        if for_base and for_cur:
            return _yougen_join(p, punits, mu, idx + 1, prev + mu.value)
    if p.dousi_split_teru:
        for_base = bmu.hinsi in ("動詞", "助動詞") and bmu.conj_form in ("連用形", "連用タ接続")
        for_cur = mu.comp_hinsi("動詞", "非自立") and mu.base_form in ("てる", "でる")
        if for_base and for_cur:
            return idx + 1, prev + mu.value[0], Unit([Segment(mu.value[1:])])
    return idx, prev, None


def _stop_cond(mu: MecabUnit) -> bool:
    return mu.hinsi_type() in (HinsiType.ZYOSI, HinsiType.SYMBOL)


def _handle_yougen(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit, Unit | None]:
    def find_reading(word: str, base_word: str, base_reading: str):
        if word == base_word:
            return base_reading
        if is_kana(word):
            return word

        i_break = False
        for i, (wc, bwc) in enumerate(zip(word, base_word)):
            if wc != bwc:
                i_break = True
                break

        return base_reading[:-1] + (word[i:] if i_break else "")

    mu = cast(MecabUnit, punits[idx])

    m = find_longest_match(dic, idx, punits, p.prefer_accent_lookups, _stop_cond)
    if m:
        tail_mu = cast(MecabUnit, punits[m.last_idx])
        res = m.lookup.results[0]
        if tail_mu.hinsi_type() != HinsiType.YOUGEN:
            return m.last_idx + 1, Unit([Segment(m.word, res.reading)], res.accents), None
        else:
            def has_special_reading(munit: MecabUnit) -> bool:
                match munit.hinsi:
                    case "動詞":
                        return munit.base_form in ("くる", "来る", "來る")
                    case "形容詞":
                        return munit.base_form in ("いい", "良い", "好い", "善い", "佳い", "吉い", "宜い")
                return False

            new_idx, trailing, split_unit = _yougen_join(p, punits, tail_mu, m.last_idx + 1)
            word_reading = find_reading(m.word, m.base_word, res.reading)
            if has_special_reading(tail_mu):
                word_reading = to_hiragana(word_reading[:-len(tail_mu.reading)] + tail_mu.reading)
            word_reading += trailing
            return new_idx, Unit([Segment(m.word + trailing, word_reading)], res.accents, res.reading), split_unit
    else:
        return idx + 1, Unit([Segment(mu.value, mu.reading)], base_form=_yougen_base_reading(mu)), None


def _handle_other(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit]:
    m = find_longest_match(dic, idx, punits, p.prefer_accent_lookups, _stop_cond)
    if m:
        res = m.lookup.results[0]
        return m.last_idx + 1, Unit([Segment(m.word, res.reading)], res.accents)
    else:
        mu = cast(MecabUnit, punits[idx])
        return idx + 1, Unit([Segment(mu.value, mu.reading)])


def convert(txt: str, prefs: ConvPrefs, mecab: Mecab, dic: Dictionary) -> list[Unit]:
    punits = mecab.analyze(txt)
    units: list[Unit] = []
    split_unit = None
    i = 0
    while i < len(punits):
        pu = punits[i]
        if isinstance(pu, MecabUnit):
            match pu.hinsi_type():
                case HinsiType.ZYOSI:
                    unit = _handle_josi(pu)
                    i += 1
                case HinsiType.YOUGEN:
                    i, unit, split_unit = _handle_yougen(prefs, dic, punits, i)
                case HinsiType.SYMBOL:
                    unit = Unit([Segment(pu.value)])
                    i += 1
                case _:
                    i, unit = _handle_other(prefs, dic, punits, i)
        else:
            unit = Unit([Segment(pu.value)])
            i += 1
        if split_unit:
            units.append(split_unit)
            split_unit = None
        units.append(unit)
    return units
