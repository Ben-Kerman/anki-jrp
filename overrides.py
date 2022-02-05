from dataclasses import dataclass

from util import ConfigError, check_json_value


@dataclass
class IgnoreOverride:
    variants: list[str]
    reading: str | None = None

    @classmethod
    def from_json(cls, obj: dict) -> "IgnoreOverride":
        variants = check_json_value(obj, "variants", list, str, True)
        reading = check_json_value(obj, "reading", str)
        return cls(variants, reading)


@dataclass
class WordOverride:
    old_variants: list[str]
    old_reading: str | None
    new_variants: list[str] | None
    new_reading: str | None

    @classmethod
    def from_json(cls, obj: dict) -> "WordOverride":
        old_variants = check_json_value(obj, "old_variants", list, str, True)
        old_reading = check_json_value(obj, "old_reading", str)
        new_variants = check_json_value(obj, "new_variants", list, str)
        new_reading = check_json_value(obj, "new_reading", str)
        if not new_variants and not new_reading:
            raise ConfigError("new variant list and new reading can't both be missing")
        return cls(old_variants, old_reading, new_variants, new_reading)


@dataclass
class AccentOverride:
    variants: list[str]
    reading: str
    accents: list[int]

    @classmethod
    def from_json(cls, obj: dict) -> "AccentOverride":
        variants = check_json_value(obj, "variants", list, str, True)
        reading = check_json_value(obj, "reading", str, required=True)
        accents = check_json_value(obj, "accents", list, int, True)
        return cls(variants, reading, accents)
