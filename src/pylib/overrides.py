import json
from collections.abc import Generator
from dataclasses import dataclass
from typing import Generic, Type, TypeVar, Union

from .normalize import comp_kana
from .util import ConfigError, from_json, get_path


@dataclass
class IgnoreOverride:
    variants: list[str]
    reading: str | None = None

    def fmt(self) -> str:
        return f"ignore {self.reading or ''}【{'・'.join(self.variants)}】"

    def match(self, variant: str, reading: str | None) -> bool:
        return variant in self.variants and (not self.reading or not reading or comp_kana(reading, self.reading))


@dataclass
class WordOverride:
    old_variants: list[str]
    old_reading: str | None = None
    new_variants: list[str] | None = None
    new_reading: str | None = None
    pre_lookup: bool = False
    post_lookup: bool = True

    def fmt(self) -> str:
        old_vars = f"【{'・'.join(self.old_variants)}】" if self.old_variants else ""
        new_vars = f"【{'・'.join(self.new_variants)}】" if self.new_variants else ""
        return f"{self.old_reading or ''}{old_vars}→ {self.new_reading or ''}{new_vars}"

    def apply(self, variant: str, reading: str | None) -> Generator[tuple[str, str | None]] | None:
        if variant in self.old_variants \
                and (not self.old_reading or not reading or comp_kana(reading, self.old_reading)):
            new_variants = self.new_variants or (variant,)
            return ((nv, self.new_reading or reading) for nv in new_variants)
        else:
            return None

    @classmethod
    def from_json(cls, obj: dict) -> Union["WordOverride", ConfigError]:
        val = from_json(obj, cls, False)
        if not val.new_variants and not val.new_reading:
            return ConfigError("either new variant list or new reading is required")
        return val


@dataclass
class AccentOverride:
    variants: list[str]
    reading: str
    accents: list[int]

    def fmt(self) -> str:
        return f"{self.reading}【{'・'.join(self.variants)}】→ [{']['.join(map(str, self.accents))}]"

    def match(self, variant: str, reading: str) -> bool:
        return variant in self.variants and comp_kana(reading, self.reading)


T = TypeVar("T", IgnoreOverride, WordOverride, AccentOverride)


@dataclass
class DefaultOverride(Generic[T]):
    id: int
    value: T

    @classmethod
    def from_json(cls, typ: Type[T], obj: dict) -> "DefaultOverride":
        return cls(obj["id"], from_json(obj, typ))


@dataclass
class DefaultOverrides:
    ignore: list[DefaultOverride[IgnoreOverride]]
    word: list[DefaultOverride[WordOverride]]
    accent: list[DefaultOverride[AccentOverride]]

    @classmethod
    def load(cls):
        with open(get_path(__file__, "default_overrides.json")) as fd:
            obj = json.load(fd)
        ignore = [DefaultOverride.from_json(IgnoreOverride, e) for e in obj["ignore"]]
        word = [DefaultOverride.from_json(WordOverride, e) for e in obj["word"]]
        accent = [DefaultOverride.from_json(AccentOverride, e) for e in obj["accent"]]
        return cls(ignore, word, accent)


_def_or_inst = None


def defaults() -> DefaultOverrides:
    global _def_or_inst
    if not _def_or_inst:
        _def_or_inst = DefaultOverrides.load()
    return _def_or_inst