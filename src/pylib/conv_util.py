# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import re
from typing import Optional

from .output import OutputType

_nl_re = re.compile(r"[^\S\r\n]*[\r\n]+[^\S\r\n]*")


def squash_newlines(val: str) -> str:
    return _nl_re.sub(" ", val)


_brace_re = re.compile(r"(?:^|[^\\]){")
_tag_re = re.compile(r"(?:^|[^\\])\[((?:[^]]|\\])+)]")


def detect_syntax(val: str) -> Optional[OutputType]:
    if _brace_re.search(val):
        return OutputType.DEFAULT
    elif m := _tag_re.search(val):
        g = m.group(1)
        if "|" in g or "=" in g:
            return OutputType.DEFAULT
        else:
            return OutputType.MIGAKU
    elif len(val) and val.count(" ") / len(val) > 0.2:
        return OutputType.MIGAKU
    return None
