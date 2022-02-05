from dataclasses import dataclass

from overrides import AccentOverride, IgnoreOverride, WordOverride
from util import check_json_value


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
