from dataclasses import dataclass
from typing import Generic, TypeVar

from .accents import Accent
from .overrides import AccentOverride, IgnoreOverride, WordOverride

T = TypeVar("T", IgnoreOverride, WordOverride, AccentOverride)


@dataclass
class DefaultOverride(Generic[T]):
    id: int
    value: T


@dataclass
class DefaultOverrides:
    ignore: list[DefaultOverride[IgnoreOverride]]
    word: list[DefaultOverride[WordOverride]]
    accent: list[DefaultOverride[AccentOverride]]


ignore = [
    DefaultOverride(0, IgnoreOverride(["する"])),
    DefaultOverride(1, IgnoreOverride(["いる"])),
    DefaultOverride(2, IgnoreOverride(["ある"])),
    DefaultOverride(3, IgnoreOverride(["ない"])),
]

word = [
    DefaultOverride(0, WordOverride(["後"], new_reading="あと", pre_lookup=True, post_lookup=False))
]

accent = [
    DefaultOverride(0, AccentOverride(["する"], "する", [Accent(0)])),
    DefaultOverride(1, AccentOverride(["巨人"], "きょじん", [Accent(0)]))
]
