# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import json
import os.path
import platform
from dataclasses import dataclass, field
from itertools import chain
from json import JSONDecodeError
from typing import Iterable, List, Optional, Set, Tuple, Union

from . import default_overrides, version
from .accents import Accent
from .overrides import AccentOverride, IgnoreOverride, WordOverride
from .util import ConfigError, from_json, to_json


@dataclass
class StylePrefs:
    hide_on_front: bool = True
    use_diamond_indicators: bool = False
    highlight_split_accents: bool = True
    ruby_font_size: str = "40%"
    graph_font_size: str = "70%"
    heiban: str = "#7070ff"
    kifuku: str = "#ffff00"
    atamadaka: str = "#00a000"
    odaka: str = "#ff77ff"
    nakadaka: str = "#c75000"
    unknown: str = "#808080"
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
    indicator_bar_offset: str = "0em"
    indicator_bar_offset_vert: str = "0.1em"
    indicator_diamond_size: str = "1em"


@dataclass
class NoteTypePrefs:
    nt_id: int
    manage_script: bool = True
    manage_style: bool = True
    style: StylePrefs = field(default_factory=StylePrefs)

    @classmethod
    def default(cls) -> "NoteTypePrefs":
        return cls(0)


@dataclass
class AddonPrefs:
    mecab_path: str = os.path.join("bin", "mecab.exe")
    mecab_dict_dir: str = os.path.join("data", "ipadic")
    mecab_use_system_exe: bool = platform.system() != "Windows"
    mecab_use_system_dict: bool = False
    note_types: List[NoteTypePrefs] = field(default_factory=list)


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
    ignore: List[IgnoreOverride] = field(default_factory=list)
    word: List[WordOverride] = field(default_factory=list)
    accent: List[AccentOverride] = field(default_factory=list)


@dataclass
class DisabledOverrideIds:
    ignore: Set[int] = field(default_factory=set)
    word: Set[int] = field(default_factory=set)
    accent: Set[int] = field(default_factory=set)

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

    def match_ignore_or(self, variant: str, reading: Optional[str]) -> bool:
        defaults = (do.value for do in default_overrides.ignore if do.id not in self.disabled_override_ids.ignore)
        return any(io.match(variant, reading) for io in chain(self.overrides.ignore, defaults))

    def apply_word_or(self, variant: str, reading: Optional[str],
                      is_pre: bool = False) -> Optional[Iterable[Tuple[str, Optional[str]]]]:
        defaults = (do.value for do in default_overrides.word if do.id not in self.disabled_override_ids.word)
        for wo in (wo for wo in chain(self.overrides.word, defaults)):
            if is_pre and wo.pre_lookup or not is_pre and wo.post_lookup:
                if gen := wo.apply(variant, reading):
                    return gen
        return None

    def apply_accent_or(self, variant: str, reading: str) -> Optional[List[Accent]]:
        defaults = (ao.value for ao in default_overrides.accent if ao.id not in self.disabled_override_ids.accent)
        for ao in chain(self.overrides.accent, defaults):
            if ao.match(variant, reading):
                return ao.accents
        return None


@dataclass
class OutputPrefs:
    min_accent_moras: int = 3
    katakana_min_accent: bool = False
    preserve_spaces: bool = True


@dataclass
class Prefs:
    convert: ConvPrefs = field(default_factory=ConvPrefs)
    output: OutputPrefs = field(default_factory=OutputPrefs)
    addon: AddonPrefs = field(default_factory=AddonPrefs)

    @classmethod
    def load_from_file(cls, path: str) -> Union["Prefs", ConfigError, None]:
        if not os.path.exists(path):
            return None

        with open(path, encoding="utf-8") as cfd:
            try:
                raw = json.load(cfd)
            except JSONDecodeError as e:
                return ConfigError(f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}")
        return from_json(raw, cls)

    def write_to_file(self, path: str):
        json_obj = to_json(self, type(self)())
        json_obj["version"] = version.config
        json_str = json.dumps(json_obj, ensure_ascii=False)
        with open(path, "w", encoding="utf-8") as cfd:
            cfd.write(json_str)
