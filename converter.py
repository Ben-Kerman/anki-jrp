from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import cast

from dictionary import Dictionary, Lookup
from mecab import HinsiType, Mecab, MecabUnit, ParserUnit
from normalize import is_kana, to_hiragana
from preferences import ConvPrefs, JoinPrefs
from segments import Segment, Unit


@dataclass
class Match:
    last_idx: int
    word: str
    base_word: str | None = None
    lookup: Lookup = None

    def gen_unit_if_ignored(self) -> Unit | None:
        return None if self.lookup else Unit([Segment(self.word)])


def _dsc(_) -> bool:
    return False


_potential_table = str.maketrans("えけげせてねべめれエケゲセテネベメレ",
                                 "うくぐすつぬぶむるうくぐすつぬぶむる")


def base_for_potential(word: str, reading: str | None) -> tuple[str, str] | None:
    if len(word) < 3 or word[-1] != "る":
        return None
    base_end = word[-2].translate(_potential_table)
    return word[:-2] + base_end, reading and reading[:-2] + base_end


def find_longest_match(prefs: ConvPrefs, dic: Dictionary, idx: int, punits: list[ParserUnit],
                       stop_cond: Callable[[MecabUnit], bool] = _dsc) -> Match | None:
    def lookup_variants(p: ConvPrefs, word: str, reading_guess: str | None,
                        base_word: str | None = None) -> Generator[tuple[str, str | None, str | None]]:
        def pot(word: str, reading: str | None) -> tuple[str, str, str] | None:
            if res := base_for_potential(word, reading):
                pot_base, pot_reading = res
                return pot_base, pot_reading, pot_base

        if base_word:
            if or_gen := p.apply_word_or(base_word, reading_guess, is_pre=True):
                for or_var, or_reading in or_gen:
                    yield or_var, or_reading, or_var
            else:
                yield base_word, reading_guess, base_word
                if pot_res := pot(base_word, reading_guess):
                    yield pot_res
        if or_gen := p.apply_word_or(word, reading_guess, is_pre=True):
            for or_var, or_reading in or_gen:
                yield or_var, or_reading, None
        else:
            yield word, reading_guess, None
            if pot_res := pot(word, reading_guess):
                yield pot_res

    acc_match: Match | None = None
    plain_match: Match | None = None
    for i in range(idx, len(punits)):
        pu = punits[i]
        if not isinstance(pu, MecabUnit) or stop_cond(pu):
            break

        if all(isinstance(u, MecabUnit) and u.hinsi != "未知語" for u in punits[idx:i + 1]):
            reading_guess = "".join(map(lambda u: u.reading, punits[idx:i]))
            reading_guess += pu.base_reading() or pu.reading
        else:
            reading_guess = None
        part_word = "".join(map(lambda u: u.value, punits[idx:i]))
        word = part_word + pu.value
        base_word = part_word + pu.base_form if pu.hinsi_type() == HinsiType.YOUGEN else None

        for var_word, var_guess, var_base in lookup_variants(prefs, word, reading_guess, base_word):
            if lu := dic.look_up(var_word, var_guess):
                match = Match(i, word, var_base, lu)
                if lu.has_accents():
                    acc_match = match
                else:
                    plain_match = match
                break

    def find_retval(prefs: ConvPrefs, acc: Match, plain: Match) -> Match:
        if acc:
            if prefs.prefer_accent_lookups:
                return acc
            elif plain and plain.last_idx > acc.last_idx:
                return plain
            else:
                return acc
        else:
            return plain

    rv = find_retval(prefs, acc_match, plain_match)
    if rv:
        if prefs.match_ignore_or(rv.base_word or rv.word, rv.lookup.results[0].reading):
            rv.base_word = None
            rv.lookup = None
        else:
            if gen := prefs.apply_word_or(rv.base_word or rv.word, rv.lookup.results[0].reading):
                for var, reading in gen:
                    if lu := dic.look_up(var, reading):
                        return Match(rv.last_idx, rv.word, rv.base_word, lu)
                    else:
                        return None
    return rv


def _handle_josi(munit: MecabUnit) -> Unit:
    if to_hiragana(munit.value) == to_hiragana(munit.reading):
        return Unit([Segment(munit.value)])
    else:
        return Unit.from_text(munit.value, to_hiragana(munit.reading))


def _yougen_join(p: JoinPrefs, punits: list[ParserUnit], bmu: MecabUnit,
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
            split_val = mu.value[1:]
            return idx + 1, prev + mu.value[0], Unit([Segment(split_val)]) if split_val else None
    return idx, prev, None


def _stop_cond(mu: MecabUnit) -> bool:
    return mu.hinsi_type() in (HinsiType.ZYOSI, HinsiType.SYMBOL)


def _finalize_yougen(p: ConvPrefs, punits: list[ParserUnit], tail_mu: MecabUnit,
                     m: Match) -> tuple[int, Unit, Unit | None]:
    def find_reading(word: str, base_word: str, base_reading: str) -> str:
        def is_sahen(word: str, base: str) -> bool:
            return base.endswith("する") and word.endswith(("さ", "し", "す", "せ", "そ")) \
                   or base.endswith("ずる") and word.endswith(("じ", "ぜ"))

        if word == base_word:
            return base_reading
        if is_kana(word):
            return word

        i_break = False
        for i, (wc, bwc) in enumerate(zip(word, base_word)):
            if wc != bwc:
                i_break = True
                break

        head = base_reading[:-2 if is_sahen(word, base_word) else -1]
        tail = word[i:] if i_break else ""
        return head + tail

    def has_special_reading(munit: MecabUnit) -> bool:
        match munit.hinsi:
            case "動詞":
                return munit.base_form in ("くる", "来る", "來る")
            case "形容詞":
                return munit.base_form in ("いい", "良い", "好い", "善い", "佳い", "吉い", "宜い")
        return False

    new_idx, trailing, split_unit = _yougen_join(p.join, punits, tail_mu, m.last_idx + 1)
    if iu := m.gen_unit_if_ignored():
        iu.segments[0].text += trailing
        unit = iu
    else:
        res = m.lookup.results[0]

        word_reading = find_reading(m.word, m.base_word, res.reading)
        if has_special_reading(tail_mu):
            word_reading = to_hiragana(word_reading[:-len(tail_mu.reading)] + tail_mu.reading)
        word_reading += trailing
        word = m.word + trailing

        or_accents = p.apply_accent_or(m.base_word, res.reading)
        uncertain = not or_accents and m.lookup.uncertain
        unit = Unit.from_text(word, word_reading, res.reading, or_accents or res.accents, True, uncertain)
    return new_idx, unit, split_unit


def _finalize_other(p: ConvPrefs, m: Match) -> tuple[int, Unit, Unit | None]:
    if iu := m.gen_unit_if_ignored():
        unit = iu
    else:
        res = m.lookup.results[0]

        or_accents = p.apply_accent_or(m.word, res.reading)
        uncertain = not or_accents and m.lookup.uncertain
        unit = Unit.from_text(m.word, res.reading, accents=or_accents or res.accents, uncertain=uncertain)
    return m.last_idx + 1, unit, None


def _handle_other(p: ConvPrefs, dic: Dictionary, punits: list[ParserUnit], idx: int) -> tuple[int, Unit, Unit | None]:
    m = find_longest_match(p, dic, idx, punits, _stop_cond)
    if m:
        tail_mu = cast(MecabUnit, punits[m.last_idx])
        if tail_mu.hinsi_type() == HinsiType.YOUGEN:
            return _finalize_yougen(p, punits, tail_mu, m)
        else:
            return _finalize_other(p, m)
    else:
        mu = cast(MecabUnit, punits[idx])
        is_yougen = mu.hinsi_type() == HinsiType.YOUGEN
        base = mu.base_reading() if is_yougen else None
        return idx + 1, Unit.from_text(mu.value, mu.reading, base, is_yougen=is_yougen), None


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
                case HinsiType.SYMBOL:
                    unit = Unit([Segment(pu.value)])
                    i += 1
                case _:
                    i, unit, split_unit = _handle_other(prefs, dic, punits, i)
        else:
            unit = Unit([Segment(pu.value)])
            i += 1
        units.append(unit)
        if split_unit:
            units.append(split_unit)
            split_unit = None
    return units
