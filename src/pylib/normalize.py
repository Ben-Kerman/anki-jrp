# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
from typing import Callable, Iterable, List

_hira = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ"
_kata = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ"
_to_hira_tbl = str.maketrans(_kata, _hira)
_to_kata_tbl = str.maketrans(_hira, _kata)
_non_script_chrs = "ー・"
_is_hira_set = set(_hira + _non_script_chrs)
_is_kata_set = set(_kata + _non_script_chrs)


def _itr_conv(itr: Iterable[str], fn: Callable[[str], str]) -> List[str]:
    conv_itr = (fn(e) for e in itr)
    seen = set()
    return [e for e in conv_itr if not (e in seen or seen.add(e))]


def is_hiragana(val: str) -> bool:
    return all(c in _is_hira_set for c in val)


def has_hiragana(val: str) -> bool:
    return any(c in _is_hira_set for c in val)


def to_hiragana(val: str) -> str:
    return val.translate(_to_hira_tbl)


def itr_to_hira(itr: Iterable[str]) -> List[str]:
    return _itr_conv(itr, to_hiragana)


def is_katakana(val: str) -> bool:
    return all(c in _is_kata_set for c in val)


def has_katakana(val: str) -> bool:
    return any(c in _is_kata_set for c in val)


def to_katakana(val: str) -> str:
    return val.translate(_to_kata_tbl)


def is_kana(val: str) -> bool:
    return is_katakana(to_katakana(val))


def has_kana(val: str) -> bool:
    return any(c in _kata for c in to_katakana(val))


def comp_kana(val: str, *args: str) -> bool:
    first = to_katakana(val)
    return all(to_katakana(a) == first for a in args)


def itr_to_kata(itr: Iterable[str]) -> List[str]:
    return _itr_conv(itr, to_katakana)


_i_dan = ("キ", "ギ", "シ", "ジ", "チ", "ヂ", "ニ", "ヒ", "ビ", "ピ", "ミ", "リ")
_e_comp = ("イ", "ウ", "キ", "ギ", "ク", "グ", "シ", "ジ", "チ", "ツ", "ニ", "ヒ", "ビ", "ピ", "フ", "ミ", "リ", "ヴ")


def split_moras(reading: str, as_hira: bool = False) -> List[str]:
    conv_fn = to_hiragana if as_hira else to_katakana
    kana = to_katakana(reading)
    moras = []
    i = 0
    while i < len(kana):
        ck = kana[i]
        nk = kana[i + 1] if i + 1 < len(kana) else None
        if nk:
            if ck in _i_dan and nk in ("ャ", "ュ", "ョ") \
                    or nk == "ヮ" and ck in ("ク", "グ") \
                    or nk == "ァ" and ck in ("ツ", "フ", "ヴ") \
                    or nk == "ィ" and ck in ("ク", "グ", "ス", "ズ", "テ", "ツ", "デ", "フ", "イ", "ウ", "ヴ") \
                    or nk == "ゥ" and ck in ("ト", "ド", "ホ", "ウ") \
                    or nk == "ェ" and ck in _e_comp \
                    or nk == "ォ" and ck in ("ク", "グ", "ツ", "フ", "ウ", "ヴ") \
                    or nk == "ャ" and ck in ("フ", "ヴ") \
                    or nk == "ュ" and ck in ("テ", "デ", "フ", "ウ", "ヴ") \
                    or nk == "ョ" and ck in ("フ", "ヴ"):
                moras.append(conv_fn(ck + nk))
                i += 2
                continue
        moras.append(conv_fn(ck))
        i += 1
    return moras
