# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
from enum import Enum, auto
from typing import List, Optional, Sequence

from .normalize import is_hiragana, is_kana, split_moras
from .preferences import OutputPrefs
from .segments import Unit
from .util import escape_text as esc


class OutputType(Enum):
    DEFAULT = auto()
    MIGAKU = auto()


def _add_accent(unit: Unit, prefs: Optional[OutputPrefs]) -> bool:
    if not unit.accents:
        return False

    if not prefs:
        return True

    if len(unit.segments) == 1:
        txt = unit.segments[0].text
        if (is_hiragana(txt) or prefs.katakana_min_accent and is_kana(txt)) \
                and len(split_moras(txt)) < prefs.min_accent_moras and not unit.is_yougen:
            return False
    return True


def fmt_migaku(units: Sequence[Unit], prefs: Optional[OutputPrefs] = None) -> str:
    def fmt_unit(unit: Unit) -> str:
        segments = unit.non_base_segments()
        if len(segments) == 1 and segments[0].text.isspace():
            return segments[0].text.replace(" ", chr(0x2002))  # en space

        tag_content = ""
        if _add_accent(unit, prefs):
            if unit.is_yougen:
                tag_content += f",{esc(';]', unit.base_reading())}"
            rdng = unit.accent_reading()
            tag_content += f";{','.join(acc.fmt_migaku(rdng, unit.is_yougen) for acc in unit.accents)}"

        if len(segments) == 1 and (is_kana(segments[0].text) or not segments[0].reading):
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{esc('[', segments[0].text)}{tag}"
        elif len(segments) > 1 and is_kana(segments[-1].text):
            tag_content = esc(",;]", unit.reading(-1)) + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{esc('[', unit.text(-1))}{tag}{segments[-1].text}"
        else:
            tag_content = esc(",;]", unit.reading()) + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{esc('[', unit.text())}{tag}"

    return " ".join([fmt_unit(u) for u in units])


def insert_nbsp(val: str) -> str:
    new_chars: List[str] = []
    was_space: bool = False
    for c in val:
        if was_space:
            was_space = False
            if c == " ":
                new_chars.append(chr(0xa0))
                continue
        elif c == " ":
            was_space = True
        new_chars.append(c)
    return "".join(new_chars)


def fmt_jrp(units: Sequence[Unit], prefs: Optional[OutputPrefs] = None) -> str:
    def fmt_unit(unit: Unit) -> str:
        if _add_accent(unit, prefs):
            segment_str = "".join([s.fmt(escape=True) for s in unit.segments])
            uncert = "!" if unit.uncertain else ""
            yougen = "Y" if unit.is_yougen else ""
            sp_base = f"|{unit.special_base}" if unit.special_base else ""
            return f"{{{segment_str};{uncert}{yougen}{','.join(map(str, unit.accents))}{sp_base}}}"
        else:
            return "".join([s.fmt(escape=True, ignore_base=True) for s in unit.segments])

    res = "".join([fmt_unit(u) for u in units])
    return insert_nbsp(res) if prefs and prefs.preserve_spaces else res
