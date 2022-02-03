from collections.abc import Generator

from normalize import is_kana
from segments import Unit


def _add_accent(unit: Unit) -> bool:
    if not unit.accents:
        return False

    if len(unit.segments) == 1:
        txt = unit.segments[0].text
        if is_kana(txt) and len(txt) < 3 and not unit.base_form:
            return False
    return True


def fmt_migaku(units: list[Unit]) -> str:
    def migaku_accents(unit: Unit) -> Generator[str]:
        reading = unit.reading()
        for acc in unit.accents:
            if acc == 0:
                yield "h"
            elif unit.base_form:
                yield f"k{acc}"
            elif acc == 1:
                yield "a"
            elif acc == len(reading):
                yield "o"
            else:
                yield f"n{acc}"

    def fmt_unit(unit: Unit) -> str:
        if len(unit.segments) == 1 and all(c == " " for c in unit.segments[0].text):
            return chr(0x2002)  # en space

        tag_content = ""
        if _add_accent(unit):
            if unit.base_form:
                tag_content += "," + unit.base_form
            tag_content += ";" + ",".join(migaku_accents(unit))

        if len(unit.segments) == 1 and (is_kana(unit.segments[0].text) or not unit.segments[0].reading):
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{unit.segments[0].text}{tag}"
        elif len(unit.segments) > 1 and is_kana(unit.segments[-1].text):
            tag_content = unit.reading(-1) + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            tail = unit.segments[-1].text
            return f"{unit.text(-1)}{tag}{tail}"
        else:
            tag_content = unit.reading() + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{unit.text()}{tag}"

    return " ".join(map(fmt_unit, units))
