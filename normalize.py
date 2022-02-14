from collections.abc import Iterable
from typing import Callable

_hira = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ"
_kata = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ"
_to_hira_tbl = str.maketrans(_kata, _hira)
_to_kata_tbl = str.maketrans(_hira, _kata)
_non_script_chrs = "ー・"
_is_hira_set = set(_hira + _non_script_chrs)
_is_kata_set = set(_kata + _non_script_chrs)


def _itr_conv(itr: Iterable[str], fn: Callable[[str], str]) -> list[str]:
    conv_itr = (fn(e) for e in itr)
    seen = set()
    return [e for e in conv_itr if not (e in seen or seen.add(e))]


def is_hiragana(val: str) -> bool:
    return all(c in _is_hira_set for c in val)


def has_hiragana(val: str) -> bool:
    return any(c in _is_hira_set for c in val)


def to_hiragana(val: str) -> str:
    return val.translate(_to_hira_tbl)


def itr_to_hira(itr: Iterable[str]) -> list[str]:
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


def itr_to_kata(itr: Iterable[str]) -> list[str]:
    return _itr_conv(itr, to_katakana)
