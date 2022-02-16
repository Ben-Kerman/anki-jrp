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

    def check_type(val: Any, t: Type[T]) -> U | ConfigError:
        return val if type(val) is t else ConfigError(f"invalid type")

    if typ in (str, bool, int, float, NoneType):
        return check_type(json_val, typ)
    elif type(typ) == GenericAlias and get_origin(typ) in (list, set):
        lst = check_type(json_val, list)
        if isinstance(lst, ConfigError):
            return lst

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
        return set(new_lst) if get_origin(typ) is set else new_lst
    else:
        dic = check_type(json_val, dict)
        if isinstance(dic, ConfigError):
            return ConfigError("impossible JSON value")

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
                for ft in types_to_list(field.type):
                    res = from_json(field_val, ft)
                    if isinstance(res, ConfigError):
                        err = res
                    else:
                        init[field.name] = res
                        err = None
                        break
                if err:
                    return ConfigError(f"{field.name}: {err.msg}")
        return typ(**init)
