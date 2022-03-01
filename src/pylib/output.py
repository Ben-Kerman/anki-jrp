from .normalize import is_hiragana, is_kana, split_moras
from .preferences import OutputPrefs
from .segments import Unit
from .util import escape_text as esc


def _add_accent(p: OutputPrefs, unit: Unit) -> bool:
    if not unit.accents:
        return False

    if len(unit.segments) == 1:
        txt = unit.segments[0].text
        if (is_hiragana(txt) or p.katakana_min_accent and is_kana(txt)) \
                and len(split_moras(txt)) < p.min_accent_moras and not unit.is_yougen:
            return False
    return True


def fmt_migaku(units: list[Unit], prefs: OutputPrefs | None = None) -> str:
    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        segments = unit.non_base_segments()
        if len(segments) == 1 and all(c == " " for c in segments[0].text):
            return chr(0x2002) * len(segments[0].text)  # en space

        tag_content = ""
        if _add_accent(p, unit):
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

    if not prefs:
        prefs = OutputPrefs()
    return " ".join([fmt_unit(u, prefs).replace(" ", chr(0x2002)) for u in units])


def fmt_jrp(units: list[Unit], prefs: OutputPrefs | None = None) -> str:
    def fmt_unit(unit: Unit, p: OutputPrefs) -> str:
        segment_str = "".join([s.fmt(escape=True) for s in unit.segments])
        if _add_accent(p, unit):
            uncert = "!" if unit.uncertain else ""
            yougen = "Y" if unit.is_yougen else ""
            sp_base = f"|{unit.special_base}" if unit.special_base else ""
            return f"{{{segment_str};{uncert}{yougen}{','.join(map(str, unit.accents))}{sp_base}}}"
        else:
            return segment_str

    if not prefs:
        prefs = OutputPrefs()
    return "".join([fmt_unit(u, prefs) for u in units])
