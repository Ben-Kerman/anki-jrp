import dataclasses
import os.path
import re
from re import Pattern

from anki.collection import Collection
from anki.models import NotetypeDict

from ..pylib import version
from ..pylib.preferences import AddonPrefs, NoteTypePrefs


def _read_file(*path_comps: str) -> str:
    with open(os.path.join(os.path.dirname(os.path.normpath(__file__)), *path_comps)) as fd:
        return fd.read()


def _compress_spaces(data: str) -> str:
    return " ".join(line for line in (raw_line.strip() for raw_line in data.splitlines()) if line)


def generate_css(p: NoteTypePrefs) -> str:
    filenames = (("variables", "fmt"), ("unit", "css"), ("pattern", "css"),
                 ("indicator-diamond" if p.use_diamond_indicators else "indicator-bar", "css"),
                 ("graph", "css"))
    stylesheets: dict[str, str] = {name: _read_file("..", "style", f"{name}.{ext}") for name, ext in filenames}
    stylesheets["variables"] = stylesheets["variables"].format(**dataclasses.asdict(p.style))
    return _compress_spaces("".join(stylesheets[fn] for fn, _ in filenames))


def generate_js() -> str:
    return f"(function(){{ {_compress_spaces(_read_file('js', 'cards.js'))} }})();"


_trail_str = "Do Not Edit If Using Automatic CSS and JS Management"
_css_re = re.compile(rf"\n*/\*###((?:MIA|MIGAKU) JAPANESE SUPPORT) CSS STARTS###\n"
                     rf"{_trail_str}\*/\n.*?\n/\*###\1 CSS ENDS###\*/\n*")
_js_re = re.compile(rf"\n*<!--###((?:MIA|MIGAKU) JAPANESE SUPPORT) ((?:(?:KATAKANA )?CONVERTER )?JS) START###\n"
                    rf"{_trail_str}-->.*?<!--###\1 \2 ENDS###-->\n*")


def _remove_mia_migaku(value: str, css: bool = False) -> str:
    return (_css_re if css else _js_re).sub("", value)


_comment_symbols = {
    "html": ("<!--", "-->"),
    "css": ("/*", "*/")
}


def enclose_code(code: str, css: bool = False) -> str:
    oc, cc = _comment_symbols["css" if css else "html"]
    return f"{oc} JRP add-on managed section start [version:{0}] {cc}\n" \
           f"{oc} Changing the opening and closing tags in any way will break automatic CSS/JS handling.\n" \
           f"{' ' * len(oc)} Any manual changes made within this section will be overwritten. {cc}\n" \
           f"{code}\n" \
           f"{oc} JRP add-on managed section end {cc}"


def _split_managed_section(value: str, css: bool = False) -> tuple[str, str] | None:
    def tag_re(end: bool = False) -> Pattern:
        oc, cc = [re.escape(c) for c in _comment_symbols["css" if css else "html"]]
        tag_pat = "end" if end else r"start \[version:(\d+)]"
        return re.compile(rf"^[^\S\r\n]*{oc} JRP add-on managed section {tag_pat} {cc}[^\S\r\n]*$", re.M)

    if start_m := tag_re().search(value):
        if int(start_m.group(1)) == (version.css if css else version.js):
            return None
        if end_m := tag_re(end=True).search(value, start_m.end()):
            return value[:start_m.start()], value[end_m.end():]

    return f"{value.rstrip()}\n\n", ""


def update_style(nt: NotetypeDict, prefs: NoteTypePrefs) -> NotetypeDict | None:
    def update_css(css: str) -> str | None:
        if prefs.remove_mia_migaku:
            css = _remove_mia_migaku(css, css=True)
        if sects := _split_managed_section(css, css=True):
            before, after = sects
            return f"{before}{enclose_code(generate_css(prefs), css=True)}{after}"
        else:
            return None

    new_css = update_css(nt["css"])
    if new_css:
        nt["css"] = new_css
        return nt
    else:
        return None


def update_script(nt: NotetypeDict, prefs: NoteTypePrefs) -> NotetypeDict | None:
    def update_js(fmt: str) -> str | None:
        if prefs.remove_mia_migaku:
            fmt = _remove_mia_migaku(fmt)
        if sects := _split_managed_section(fmt):
            before, after = sects
            return f"{before}{enclose_code(f'<script>{generate_js()}</script>')}{after}"
        else:
            return None

    had_changes = False
    for tpl in nt["tmpls"]:
        for fmt_name in ("qfmt", "afmt"):
            new_fmt = update_js(tpl[fmt_name])
            if new_fmt:
                had_changes = True
                tpl[fmt_name] = new_fmt

    return nt if had_changes else None


def update_templates(nt: NotetypeDict, prefs: NoteTypePrefs) -> NotetypeDict | None:
    had_changes = False
    if prefs.manage_style:
        if with_style := update_style(nt, prefs):
            had_changes = True
            nt = with_style

    if prefs.manage_script:
        if with_script := update_script(nt, prefs):
            had_changes = True
            nt = with_script

    return nt if had_changes else None


def update_notetypes(col: Collection, prefs: AddonPrefs) -> None:
    for nt_prefs in prefs.note_types:
        nt = col.models.get(nt_prefs.nt_id)
        if not nt:
            # TODO report error
            continue

        nt = update_templates(nt, nt_prefs)
        if nt:
            try:
                col.models.update_dict(nt)
            except Exception as e:
                # TODO report error
                pass
