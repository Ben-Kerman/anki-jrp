import dataclasses
import os.path
import re

from anki.collection import Collection

from preferences import NoteTypePrefs


def _read_file(*path_comps: str) -> str:
    with open(os.path.join(os.path.dirname(__file__), *path_comps)) as fd:
        return fd.read()


def _compress_spaces(data: str) -> str:
    return " ".join(line for line in (raw_line.strip() for raw_line in data.splitlines()) if line)


def generate_css(p: NoteTypePrefs) -> str:
    filenames = (("variables", "fmt"), ("unit", "css"), ("pattern", "css"),
                 ("indicator-diamond" if p.use_diamond_indicators else "indicator-bar", "css"),
                 ("graph", "css"))
    stylesheets: dict[str, str] = {name: _read_file("style", f"{name}.{ext}") for name, ext in filenames}
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


def update_template(col: Collection, note_type_id: int, prefs: NoteTypePrefs) -> bool:
    nt = col.models.get(note_type_id)
    if not nt:
        return False

    if prefs.manage_style:
        css = nt["css"]
        if prefs.remove_mia_migaku:
            css = _remove_mia_migaku(css, css=True)
        nt["css"] = f"{css}\n\n{generate_css(prefs)}"

    if prefs.manage_script:
        for tpl in nt["tmpls"]:
            for fmt_name in ("qfmt", "afmt"):
                fmt = tpl[fmt_name]
                if prefs.remove_mia_migaku:
                    fmt = _remove_mia_migaku(fmt)
                tpl[fmt_name] = f"{fmt}\n\n<script>{generate_js()}</script>"

    try:
        col.models.update_dict(nt)
        return True
    except Exception as e:
        return False  # TODO report error
