from collections.abc import Generator

from normalize import is_hiragana, is_kana
from preferences import OutputPrefs
from segments import Unit
from util import split_moras


class OutputError(Exception):
    pass


def _add_accent(p: OutputPrefs, unit: Unit) -> bool:
    if not unit.accents:
        return False

    if len(unit.segments) == 1:
        txt = unit.segments[0].text
        if (is_hiragana(txt) or p.katakana_min_accent and is_kana(txt)) \
                and len(split_moras(txt)) < p.min_accent_moras and not unit.base_form:
            return False
    return True


def fmt_migaku(units: list[Unit], prefs: OutputPrefs) -> str:
    def migaku_accents(unit: Unit) -> Generator[str]:
        moras = split_moras(unit.reading())
        for acc in unit.accents:
            if acc == 0:
                yield "h"
            elif unit.is_yougen:
                yield f"k{acc}"
            elif acc == 1:
                yield "a"
            elif acc == len(moras):
                yield "o"
            else:
                yield f"n{acc}"

    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        segments = unit.non_base_segments()
        if len(segments) == 1 and all(c == " " for c in segments[0].text):
            return chr(0x2002)  # en space

        tag_content = ""
        if _add_accent(p, unit):
            if unit.is_yougen:
                tag_content += "," + unit.base_form()
            tag_content += ";" + ",".join(migaku_accents(unit))

        if len(segments) == 1 and (is_kana(segments[0].text) or not segments[0].reading):
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{segments[0].text}{tag}"
        elif len(segments) > 1 and is_kana(segments[-1].text):
            tag_content = unit.reading(-1) + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            tail = segments[-1].text
            return f"{unit.text(-1)}{tag}{tail}"
        else:
            tag_content = unit.reading() + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{unit.text()}{tag}"

    if not prefs:
        prefs = OutputPrefs()
    return " ".join([fmt_unit(u, prefs) for u in units])


def fmt_jrp(units: list[Unit], prefs: OutputPrefs | None = None) -> str:
    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        def accent_strs(u: Unit) -> Generator[str]:
            if u.is_yougen:
                moras = len(split_moras(u.base_form()))
                for acc in u.accents:
                    yield str(acc - moras - 1) if acc != 0 else "0"
            else:
                for acc in u.accents:
                    yield str(acc)

        segment_str = "".join([s.fmt() for s in unit.segments])
        if _add_accent(p, unit):
            uncert = "!" if unit.uncertain else ""
            yougen = "Y" if unit.is_yougen else ""
            sp_base = f"|{unit.special_base}" if unit.special_base else ""
            return f"{{{segment_str};{uncert}{yougen}{','.join(accent_strs(unit))}{sp_base}}}"
        else:
            return segment_str

    if not prefs:
        prefs = OutputPrefs()
    return "".join([fmt_unit(u, prefs) for u in units])
