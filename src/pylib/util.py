import dataclasses
import sys
from dataclasses import MISSING, dataclass, is_dataclass
from types import GenericAlias, NoneType, UnionType
from typing import Any, Iterable, Type, TypeVar, get_args, get_origin


def warn(*args):
    print(*args, file=sys.stderr)


@dataclass
class ConfigError:
    msg: str


T = TypeVar("T")
U = TypeVar("U")


def escape_text(chrs: Iterable[str], txt: str) -> str:
    dic = {c: f"\\{c}" for c in chrs}
    dic["\\"] = r"\\"
    return txt.translate(str.maketrans(dic))


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
        if try_cls_method:
            try:
                return typ.from_json(json_val)
            except AttributeError:
                pass

        dic = check_type(json_val, dict)
        if isinstance(dic, ConfigError):
            return ConfigError("impossible JSON value")

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


class ConvIgnore:
    pass


def to_json(value: T, default: T | None = None, try_cls_method: bool = True) -> Any:
    typ = type(value)

    if value == default or value is None:
        return ConvIgnore
    elif typ in (str, bool, int, float):
        return value
    elif typ in (list, set):
        def conv_val(val: Any) -> Any:
            if hasattr(val, "default"):
                if val.default:
                    return to_json(val, val.default())
            elif is_dataclass(val):
                return to_json(val, type(val)())

            return to_json(val)

        return [conv_val(e) for e in value]
    else:
        if try_cls_method:
            try:
                return value.to_json(default)
            except AttributeError:
                pass

        dic = {}
        for field in dataclasses.fields(typ):
            if default is None:
                res = to_json(getattr(value, field.name))
            else:
                res = to_json(getattr(value, field.name), getattr(default, field.name))
            if res is not ConvIgnore:
                dic[field.name] = res
        return dic
