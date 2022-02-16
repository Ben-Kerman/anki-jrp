import dataclasses
import os.path
import sys
from dataclasses import MISSING, dataclass
from types import GenericAlias, NoneType, UnionType
from typing import Any, Type, TypeVar, get_args, get_origin


def warn(*args):
    print(*args, file=sys.stderr)


def get_path(*comps: str) -> str:
    return os.path.join(os.path.dirname(__file__), *comps)


def empty_list() -> list:
    return []


@dataclass
class ConfigError:
    msg: str


T = TypeVar("T")
U = TypeVar("U")


def from_json(json_val: Any, typ: Type[T], try_cls_method: bool = True) -> T | ConfigError:
    def types_to_list(t: Any) -> tuple:
        return get_args(t) if type(t) == UnionType else (t,)

    def check_type(val: Any, expected: Type[T], actual: Type[U]) -> U | ConfigError:
        return val if expected == actual else ConfigError(f"invalid type (value: {val})")

    match json_val:
        case str(s):
            return check_type(s, typ, str)
        case bool(b):
            return check_type(b, typ, bool)
        case int(i):
            return check_type(i, typ, int)
        case float(f):
            return check_type(f, typ, float)
        case None:
            if typ is NoneType:
                return None
            else:
                return ConfigError("missing value")
        case list(lst):
            if type(typ) == GenericAlias and get_origin(typ) in (list, set):
                elem_types = types_to_list(get_args(typ)[0])

                new_lst: list = []
                err = None
                for i, e in enumerate(lst):
                    for et in elem_types:
                        res = from_json(e, et)
                        if isinstance(res, ConfigError):
                            err = res
                        else:
                            new_lst.append(res)
                            err = None
                            break
                    else:
                        break

                if err:
                    return ConfigError(f"[{i}]: {err.msg}")
                if get_origin(typ) is set:
                    return set(new_lst)
                else:
                    return new_lst
            else:
                return ConfigError("invalid type")
        case dict(dic):
            if try_cls_method:
                try:
                    return typ.from_json(dic)
                except AttributeError:
                    pass

            init = {}
            for field in dataclasses.fields(typ):
                if field.name not in dic:
                    if field.default is MISSING and field.default_factory is MISSING:
                        return ConfigError("missing value")
                    else:
                        continue
                else:
                    field_val = dic[field.name]
                    err = None
                    for t in types_to_list(field.type):
                        res = from_json(field_val, t)
                        if isinstance(res, ConfigError):
                            err = res
                        else:
                            init[field.name] = res
                            err = None
                            break
                    if err:
                        return ConfigError(f"{field.name}: {err.msg}")
            return typ(**init)
        case _:
            return ConfigError("impossible JSON value")
