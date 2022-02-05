import dataclasses
import json
from dataclasses import dataclass

from overrides import AccentOverride, IgnoreOverride, WordOverride
from util import check_json_value, get_path


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

    @classmethod
    def from_json(cls, obj: dict) -> "JoinPrefs":
        kwargs = {f.name: check_json_value(obj, f.name, bool) for f in dataclasses.fields(cls)}
        return cls(**kwargs)


@dataclass
class Overrides:
    ignore: list[IgnoreOverride]
    word: list[WordOverride]
    accent: list[AccentOverride]

    @classmethod
    def from_json(cls, obj: dict):
        ignore = [IgnoreOverride.from_json(e) for e in check_json_value(obj, "ignore", list, dict, True)]
        word = [WordOverride.from_json(e) for e in check_json_value(obj, "word", list, dict, True)]
        accent = [AccentOverride.from_json(e) for e in check_json_value(obj, "accent", list, dict, True)]
        return cls(ignore, word, accent)


@dataclass
class ConvPrefs:
    join: JoinPrefs
    overrides: Overrides
    prefer_accent_lookups: bool = False

    @classmethod
    def from_json(cls, obj: dict) -> "ConvPrefs":
        join = JoinPrefs.from_json(check_json_value(obj, "join", dict))
        overrides = Overrides.from_json(check_json_value(obj, "overrides", dict, required=True))
        pal = check_json_value(obj, "prefer_accent_lookups", bool)
        return cls(join, overrides, pal)


@dataclass
class Prefs:
    conv: ConvPrefs

    @classmethod
    def load_from_file(cls) -> "Prefs":
        with open(get_path("user_files", "config.json")) as cfd:
            raw = json.load(cfd)
        convert = ConvPrefs.from_json(check_json_value(raw, "convert", dict, required=True))
        return cls(convert)
