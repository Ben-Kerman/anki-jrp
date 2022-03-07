# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
from dataclasses import dataclass
from typing import Generic, List, TypeVar

from .accents import Accent
from .overrides import AccentOverride, IgnoreOverride, WordOverride

T = TypeVar("T", IgnoreOverride, WordOverride, AccentOverride)


@dataclass
class DefaultOverride(Generic[T]):
    id: int
    value: T


@dataclass
class DefaultOverrides:
    ignore: List[DefaultOverride[IgnoreOverride]]
    word: List[DefaultOverride[WordOverride]]
    accent: List[DefaultOverride[AccentOverride]]


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
