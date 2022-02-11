from collections.abc import Generator

from normalize import is_hiragana, is_kana, to_katakana
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
                and len(split_moras(txt)) < p.min_accent_mora and not unit.base_form:
            return False
    return True


def fmt_migaku(units: list[Unit], p: OutputPrefs) -> str:
    def migaku_accents(unit: Unit) -> Generator[str]:
        moras = split_moras(unit.reading())
        for acc in unit.accents:
            if acc == 0:
                yield "h"
            elif unit.base_form:
                yield f"k{acc}"
            elif acc == 1:
                yield "a"
            elif acc == len(moras):
                yield "o"
            else:
                yield f"n{acc}"

    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        if len(unit.segments) == 1 and all(c == " " for c in unit.segments[0].text):
            return chr(0x2002)  # en space

        tag_content = ""
        if _add_accent(p, unit):
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

    if not p:
        p = OutputPrefs()
    return " ".join([fmt_unit(u, p) for u in units])


def fmt_jrp(units: list[Unit], p: OutputPrefs | None = None) -> str:
    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        def accent_strs(unit: Unit) -> Generator[str]:
            if unit.base_form:
                moras = len(split_moras(unit.base_form))
                for acc in unit.accents:
                    yield str(acc - moras - 1) if acc != 0 else "0"
            else:
                for acc in unit.accents:
                    yield str(acc)

        def segment_strs(unit: Unit, add_accent: bool) -> Generator[str]:
            base = to_katakana(unit.base_form) if unit.base_form else None
            base_idx = 0
            use_special_base = False
            for i, s in enumerate(unit.segments):
                if add_accent and not use_special_base and base:
                    for k, c in enumerate(to_katakana(s.reading or s.text)):
                        if base_idx >= len(base):
                            raise OutputError("end of base reached before end of reading")

                        if c != base[base_idx]:
                            if i < len(unit.segments) - 1:
                                use_special_base = True
                            elif s.reading:
                                raise OutputError("last segment has a reading")

                            if not use_special_base:
                                common_pref = s.text[:k]
                                if common_pref:
                                    yield common_pref
                                yield f"[{s.text[k:]}={unit.base_form[base_idx:]}]"
                                return
                        base_idx += 1

                if s.reading:
                    yield f"[{s.text}|{s.reading}]"
                else:
                    yield s.text
            if use_special_base:
                return True
            elif add_accent and base and base_idx < len(base):
                yield f"[={unit.base_form[base_idx:]}]"

        special_base = False
        itr = segment_strs(unit, _add_accent(p, unit))
        str_list = []
        try:
            while True:
                str_list.append(next(itr))
        except StopIteration as si:
            if si.value:
                special_base = True
        segment_str = "".join(str_list)
        if _add_accent(p, unit):
            sp_base = "|" + unit.base_form if special_base else ""
            return f"{{{segment_str};{'!' if unit.uncertain else ''}{','.join(accent_strs(unit))}{sp_base}}}"
        else:
            return segment_str

    if not p:
        p = OutputPrefs()
    return "".join([fmt_unit(u, p) for u in units])
