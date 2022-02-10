import os.path
import sys
from typing import Type, TypeVar


def warn(*args):
    print(*args, file=sys.stderr)


def get_path(*comps: str) -> str:
    return os.path.join(os.path.dirname(__file__), *comps)


class ConfigError(ValueError):
    pass


T = TypeVar("T")


def check_json_value(obj: dict, name: str, typ: Type[T],
                     required: bool = False, default: T | None = None) -> T | None:
    if name not in obj:
        if required:
            raise ConfigError(f"missing value: '{name}'")
        if default is not None:
            obj[name] = default
        else:
            return None
    val = obj[name]
    if type(val) != typ:
        raise ConfigError(f"invalid type: '{name}': {val}")
    return val


def check_json_list(obj: dict, name: str, typ: Type[T],
                    required: bool = False, default: list[T] | None = None) -> list[T] | None:
    val = check_json_value(obj, name, list, required, default and default)
    if val:
        if any(type(e) != typ for e in val):
            raise ConfigError(f"invalid element type: '{name}': {val}")
    return val
