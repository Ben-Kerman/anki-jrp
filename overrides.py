import json
from collections.abc import Generator
from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from util import ConfigError, check_json_list, check_json_value, get_path


@dataclass
class IgnoreOverride:
    variants: list[str]
    reading: str | None = None

    def match(self, variant: str, reading: str | None) -> bool:
        return variant in self.variants and (not self.reading or reading == self.reading)

    @classmethod
    def from_json(cls, obj: dict) -> "IgnoreOverride":
        variants = check_json_list(obj, "variants", str, True)
        reading = check_json_value(obj, "reading", str)
        return cls(variants, reading)


@dataclass
class WordOverride:
    old_variants: list[str]
    old_reading: str | None
    new_variants: list[str] | None
    new_reading: str | None
    pre_lookup: bool = False
    post_lookup: bool = True

    def apply(self, variant: str, reading: str | None) -> Generator[tuple[str, str | None]] | None:
        if variant in self.old_variants and (not self.old_reading or not reading or reading == self.old_reading):
            new_variants = self.new_variants or (variant,)
            return ((nv, self.new_reading or reading) for nv in new_variants)
        else:
            return None

    @classmethod
    def from_json(cls, obj: dict) -> "WordOverride":
        old_variants = check_json_list(obj, "old_variants", str, True)
        old_reading = check_json_value(obj, "old_reading", str)
        new_variants = check_json_list(obj, "new_variants", str)
        new_reading = check_json_value(obj, "new_reading", str)
        pre_lookup = check_json_value(obj, "pre_lookup", bool)
        post_lookup = check_json_value(obj, "post_lookup", bool)
        if not new_variants and not new_reading:
            raise ConfigError("new variant list and new reading can't both be missing")
        return cls(old_variants, old_reading, new_variants, new_reading, pre_lookup, post_lookup)


@dataclass
class AccentOverride:
    variants: list[str]
    reading: str
    accents: list[int]

    def match(self, variant: str, reading: str) -> bool:
        return variant in self.variants and reading == self.reading

    @classmethod
    def from_json(cls, obj: dict) -> "AccentOverride":
        variants = check_json_list(obj, "variants", str, True)
        reading = check_json_value(obj, "reading", str, required=True)
        accents = check_json_list(obj, "accents", int, True)
        return cls(variants, reading, accents)


T = TypeVar("T", IgnoreOverride, WordOverride, AccentOverride)


@dataclass
class DefaultOverride(Generic[T]):
    id: int
    value: T

    @classmethod
    def from_json(cls, typ: Type[T], obj: dict) -> "DefaultOverride":
        return cls(obj["id"], typ.from_json(obj))


@dataclass
class DefaultOverrides:
    ignore: list[DefaultOverride[IgnoreOverride]]
    word: list[DefaultOverride[WordOverride]]
    accent: list[DefaultOverride[AccentOverride]]

    @classmethod
    def load(cls):
        with open(get_path("default_overrides.json")) as fd:
            obj = json.load(fd)
        ignore = [DefaultOverride.from_json(IgnoreOverride, e) for e in check_json_list(obj, "ignore", dict, True)]
        word = [DefaultOverride.from_json(WordOverride, e) for e in check_json_list(obj, "word", dict, True)]
        accent = [DefaultOverride.from_json(AccentOverride, e) for e in check_json_list(obj, "accent", dict, True)]
        return cls(ignore, word, accent)
