import dataclasses
import json
import os.path
from dataclasses import dataclass, field

from overrides import AccentOverride, IgnoreOverride, WordOverride
from util import check_json_list, check_json_value, empty_list, get_path


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
        for f in dataclasses.fields(cls):
            check_json_value(obj, f.name, bool)
        return cls(**obj)


@dataclass
class Overrides:
    ignore: list[IgnoreOverride] = field(default_factory=empty_list)
    word: list[WordOverride] = field(default_factory=empty_list)
    accent: list[AccentOverride] = field(default_factory=empty_list)

    @classmethod
    def from_json(cls, obj: dict):
        ignore = [IgnoreOverride.from_json(e) for e in check_json_list(obj, "ignore", dict, True, [])]
        word = [WordOverride.from_json(e) for e in check_json_list(obj, "word", dict, True, [])]
        accent = [AccentOverride.from_json(e) for e in check_json_list(obj, "accent", dict, True, [])]
        return cls(ignore, word, accent)


@dataclass
class DisabledOverrideIds:
    ignore: list[int] = field(default_factory=empty_list)
    word: list[int] = field(default_factory=empty_list)
    accent: list[int] = field(default_factory=empty_list)

    @classmethod
    def from_json(cls, obj: dict):
        check_json_list(obj, "ignore", int)
        check_json_list(obj, "word", int)
        check_json_list(obj, "accent", int)
        return cls(**obj)


@dataclass
class ConvPrefs:
    join: JoinPrefs = field(default_factory=JoinPrefs)
    overrides: Overrides = field(default_factory=Overrides)
    disabled_override_ids: DisabledOverrideIds = field(default_factory=DisabledOverrideIds)
    prefer_accent_lookups: bool = False

    @classmethod
    def from_json(cls, obj: dict) -> "ConvPrefs":
        obj["join"] = JoinPrefs.from_json(check_json_value(obj, "join", dict, default={}))
        obj["overrides"] = Overrides.from_json(check_json_value(obj, "overrides", dict, default={}))
        disabled_ors = check_json_value(obj, "disabled_override_ids", dict, default={})
        obj["disabled_override_ids"] = DisabledOverrideIds.from_json(disabled_ors)
        check_json_value(obj, "prefer_accent_lookups", bool)
        return cls(**obj)


@dataclass
class Prefs:
    conv: ConvPrefs = field(default_factory=ConvPrefs)

    @classmethod
    def load_from_file(cls) -> "Prefs":
        path = get_path("user_files", "config.json")
        if not os.path.exists(path):
            return cls()

        with open(path) as cfd:
            raw = json.load(cfd)
        convert = ConvPrefs.from_json(check_json_value(raw, "convert", dict, required=True))
        return cls(convert)
