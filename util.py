import sys
from typing import Type, TypeVar


def warn(*args):
    print(*args, file=sys.stderr)


class ConfigError(ValueError):
    pass


T = TypeVar("T")
E = TypeVar("E")


def check_json_value(obj: dict, name: str,
                     typ: Type[T], elem_type: Type[E] | None = None,
                     required: bool = False) -> T | list[E]:
    val = obj.get(name)
    if required and val is None:
        raise ConfigError(f"missing value: '{name}'")
    if val and (type(val) != typ or (elem_type and any(type(e) != elem_type for e in val))):
        raise ConfigError(f"invalid value: '{name}'")
    return val
