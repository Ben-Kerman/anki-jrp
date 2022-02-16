import json
import os.path
from collections.abc import Generator
from dataclasses import dataclass, field
from itertools import chain

import overrides
from overrides import AccentOverride, IgnoreOverride, WordOverride
from util import empty_list, from_json, get_path


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
    ignore: list[IgnoreOverride] = field(default_factory=empty_list)
    word: list[WordOverride] = field(default_factory=empty_list)
    accent: list[AccentOverride] = field(default_factory=empty_list)


@dataclass
class DisabledOverrideIds:
    ignore: set[int] = field(default_factory=empty_list)
    word: set[int] = field(default_factory=empty_list)
    accent: set[int] = field(default_factory=empty_list)


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


@dataclass
class OutputPrefs:
    min_accent_moras: int = 3
    katakana_min_accent: bool = False


@dataclass
class Prefs:
    convert: ConvPrefs = field(default_factory=ConvPrefs)
    output: OutputPrefs = field(default_factory=OutputPrefs)

    @classmethod
    def load_from_file(cls) -> "Prefs":
        path = get_path("user_files", "config.json")
        if not os.path.exists(path):
            return cls()

        with open(path) as cfd:
            raw = json.load(cfd)
        return from_json(raw, cls)
