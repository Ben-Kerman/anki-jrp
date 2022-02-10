import dataclasses
import json
import os.path
from collections.abc import Generator
from dataclasses import dataclass, field
from itertools import chain

import overrides
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
    ignore: set[int] = field(default_factory=empty_list)
    word: set[int] = field(default_factory=empty_list)
    accent: set[int] = field(default_factory=empty_list)

    @classmethod
    def from_json(cls, obj: dict):
        names = ("ignore", "word", "accent")
        kwargs = {name: set(obj[name]) for name in names if check_json_list(obj, name, int, default=[])}
        return cls(**kwargs)


@dataclass
class ConvPrefs:
    join: JoinPrefs = field(default_factory=JoinPrefs)
    overrides: Overrides = field(default_factory=Overrides)
    disabled_override_ids: DisabledOverrideIds = field(default_factory=DisabledOverrideIds)
    prefer_accent_lookups: bool = False

    def match_ignore_or(self, variant: str, reading: str | None) -> bool:
        defaults = (do.value for do in overrides.defaults().ignore if do.id not in self.disabled_override_ids.ignore)
        return any(io.match(variant, reading) for io in chain(self.overrides.ignore, defaults))

    def apply_word_or(self, variant: str, reading: str | None,
                      is_pre: bool = False) -> Generator[tuple[str, str | None]] | None:
        defaults = (do.value for do in overrides.defaults().word if do.id not in self.disabled_override_ids.word)
        for wo in (wo for wo in chain(self.overrides.word, defaults)):
            if is_pre and wo.pre_lookup or not is_pre and wo.post_lookup:
                if gen := wo.apply(variant, reading):
                    return gen
        return None

    def apply_accent_or(self, variant: str, reading: str) -> list[int] | None:
        defaults = (ao.value for ao in overrides.defaults().accent if ao.id not in self.disabled_override_ids.accent)
        for ao in chain(self.overrides.accent, defaults):
            if ao.match(variant, reading):
                return ao.accents
        return None

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
