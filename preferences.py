from dataclasses import dataclass
from typing import Type, TypeVar

from overrides import AccentOverride, IgnoreOverride, WordOverride


class ConfigError(ValueError):
    pass


T = TypeVar("T")
E = TypeVar("E")


def check_json_value(obj: dict, name: str,
                     typ: Type[T], elem_type: Type[E] | None = None,
                     required: bool = False) -> T | list[E]:
    val = obj.get(name)
    if required and val is None:
        raise ConfigError(f"missing value: '{name}'")
    print(val, type(val), typ, elem_type)
    if val and (type(val) != typ or (elem_type and any(type(e) != elem_type for e in val))):
        raise ConfigError(f"invalid value: '{name}'")
    return val


@dataclass
class JoinPrefs:
    yougen_join_nai: bool = True
    yougen_join_u: bool = True
    yougen_join_ta: bool = True
    yougen_join_te: bool = True
    yougen_join_ba: bool = True
    yougen_join_sou: bool = True
    keiyousi_join_sa: bool = True
    dousi_join_tai: bool = True
    dousi_join_nu: bool = True
    dousi_join_n: bool = True
    dousi_join_reru: bool = True
    dousi_join_seru: bool = True
    dousi_join_masu: bool = True
    dousi_join_tyau: bool = False
    dousi_split_teru: bool = True


@dataclass
class Overrides:
    ignore: list[IgnoreOverride]
    word: list[WordOverride]
    accent: list[AccentOverride]


@dataclass
class ConvPrefs:
    join: JoinPrefs
    overrides: Overrides
    prefer_accent_lookups: bool = False


@dataclass
class Prefs:
    conv: ConvPrefs
