import json
import os.path
from collections.abc import Generator
from dataclasses import dataclass, field
from itertools import chain
from typing import Optional

from . import overrides
from .overrides import AccentOverride, IgnoreOverride, WordOverride
from .util import from_json, to_json


@dataclass
class StylePrefs:
    use_diamond_indicators: bool = False
    ruby_font_size: str = "40%"
    graph_font_size: str = "70%"
    heiban: str = "#7070ff"
    kifuku: str = "#ffff00"
    atamadaka: str = "#00a000"
    odaka: str = "#ff77ff"
    nakadaka: str = "#c75000"
    uncertain_opacity: str = "40%"
    graph_border_width: str = "0.08em"
    graph_border_radius: str = "0.25em"
    graph_bg_light: str = "#f0f0f0"
    graph_border_light: str = "black"
    graph_bg_dark: str = "black"
    graph_border_dark: str = "white"
    indicator_bar_width: str = "3px"
    indicator_bar_radius: str = "var(--jrp-indicator-bar-width)"
    indicator_bar_gap: str = "2px"
    indicator_bar_margin: str = "0.3em"
    indicator_bar_offset: str = "0.1em"
    indicator_bar_offset_vert: str = "0.3em"
    indicator_diamond_size: str = "1em"


@dataclass
class NoteTypePrefs:
    nt_id: int
    manage_script: bool = True
    manage_style: bool = True
    style: StylePrefs = field(default_factory=StylePrefs)


@dataclass
class AddonPrefs:
    note_types: list[NoteTypePrefs] = field(default_factory=list)


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
    ignore: list[IgnoreOverride] = field(default_factory=list)
    word: list[WordOverride] = field(default_factory=list)
    accent: list[AccentOverride] = field(default_factory=list)


@dataclass
class DisabledOverrideIds:
    ignore: set[int] = field(default_factory=set)
    word: set[int] = field(default_factory=set)
    accent: set[int] = field(default_factory=set)

    def to_json(self, default: "DisabledOverrideIds") -> dict:
        val: dict = to_json(self, default, False)
        for field_name in ("ignore", "word", "accent"):
            if field_name in val:
                val[field_name].sort()
        return val


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
    addon: AddonPrefs = field(default_factory=AddonPrefs)

    @classmethod
    def load_from_file(cls, path: str) -> Optional["Prefs"]:
        if not os.path.exists(path):
            return None

        with open(path) as cfd:
            raw = json.load(cfd)
        return from_json(raw, cls)

    def write_to_file(self, path: str):
        with open(path, "w") as cfd:
            json.dump(to_json(self, type(self)()), cfd, ensure_ascii=False)
