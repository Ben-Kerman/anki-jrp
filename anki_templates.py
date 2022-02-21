import dataclasses
import os.path
import re

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
    return _compress_spaces(_read_file("js", "cards.js"))


_trail_str = "Do Not Edit If Using Automatic CSS and JS Management"
_css_re = re.compile(rf"\n*/\*###((?:MIA|MIGAKU) JAPANESE SUPPORT) CSS STARTS###\n"
                     rf"{_trail_str}\*/\n.*?\n/\*###\1 CSS ENDS###\*/\n*")
_js_re = re.compile(rf"\n*<!--###((?:MIA|MIGAKU) JAPANESE SUPPORT) ((?:(?:KATAKANA )?CONVERTER )?JS) START###\n"
                    rf"{_trail_str}-->.*?<!--###\1 \2 ENDS###-->\n*")


def _remove_mia_migaku(value: str, css: bool = False) -> str:
    return (_css_re if css else _js_re).sub("", value)
