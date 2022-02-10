import os.path
import sys
from typing import Type, TypeVar

from normalize import to_katakana


def warn(*args):
    print(*args, file=sys.stderr)


def get_path(*comps: str) -> str:
    return os.path.join(os.path.dirname(__file__), *comps)


def empty_list() -> list:
    return []


class ConfigError(ValueError):
    pass


T = TypeVar("T")


def check_json_value(obj: dict, name: str, typ: Type[T],
                     required: bool = False, default: T | None = None) -> T | None:
    if name not in obj:
        if required:
            raise ConfigError(f"missing value: '{name}'")
        if default is not None:
            obj[name] = default
        else:
            return None
    val = obj[name]
    if type(val) != typ:
        raise ConfigError(f"invalid type: '{name}': {val}")
    return val


def check_json_list(obj: dict, name: str, typ: Type[T],
                    required: bool = False, default: list[T] | None = None) -> list[T] | None:
    val = check_json_value(obj, name, list, required, default and default)
    if val:
        if any(type(e) != typ for e in val):
            raise ConfigError(f"invalid element type: '{name}': {val}")
    return val


_i_dan = ("キ", "ギ", "シ", "ジ", "チ", "ヂ", "ニ", "ヒ", "ビ", "ピ", "ミ", "リ")
_e_comp = ("イ", "ウ", "キ", "ギ", "ク", "グ", "シ", "ジ", "チ", "ツ", "ニ", "ヒ", "ビ", "ピ", "フ", "ミ", "リ", "ヴ")


def split_moras(reading: str) -> list[str]:
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
                moras.append(ck + nk)
                i += 2
                continue
        moras.append(ck)
        i += 1
    return moras
