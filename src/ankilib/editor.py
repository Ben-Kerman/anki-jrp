# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
from enum import Enum, auto
from typing import Callable, Iterable, List, Optional

import aqt.utils
from aqt.editor import Editor

from . import global_vars as gv
from .util import get_path
from ..pylib.conv_util import detect_syntax, squash_newlines
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import MecabError
from ..pylib.output import OutputType, fmt_jrp, fmt_migaku, insert_nbsp
from ..pylib.segments import ParsingError, parse_jrp, parse_migaku

_js_esc = str.maketrans({
    "\r": "\\r",
    "\n": "\\n",
    "\"": "\\\"",
    "\\": "\\\\",
})


class ConversionType(Enum):
    GENERATE = auto()
    READINGS = auto()  # TODO implement
    REMOVE = auto()


def _replace(edit: Editor, transform: Callable[[str], str]):
    def update_field_html(new_html: str):
        transformed = transform(new_html)
        if transformed is None:
            return

        edit.web.page().runJavaScript(f"""(function() {{
            if(getCurrentField().codable && getCurrentField().codable.active)
                return;
            document.execCommand("selectAll");
            document.execCommand("insertHTML", false, "{transformed.translate(_js_esc)}");
        }})();""")

    edit.web.page().runJavaScript("getCurrentField().editable.fieldHTML", lambda html: update_field_html(html))


def _convert(edit: Editor, conv_type: ConversionType, out_type: Optional[OutputType] = None):
    def gen_lines(val: str) -> Iterable[str]:
        lines = strip_html(val)
        if t := detect_syntax(val):
            parser = parse_migaku if t == OutputType.MIGAKU else parse_jrp
            yield from ("".join(u.text() for u in parser(line)) for line in lines)
        else:
            yield from lines

    def transform(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None

        val = squash_newlines(val)
        if conv_type == ConversionType.REMOVE:
            return insert_nbsp("<br>".join(gen_lines(val)))
        else:
            if not out_type:
                raise ValueError("missing output type")

            if not gv.convert_check():
                return None

            try:
                formatter = fmt_migaku if out_type == OutputType.MIGAKU else fmt_jrp
                parsed_lines = (gv.mecab_handle.analyze(line) for line in gen_lines(val))
                conv_lines = (convert(pline, gv.prefs.convert, gv.dictionary) for pline in parsed_lines)
                return "<br>".join(formatter(s, gv.prefs.output) for s in conv_lines)
            except MecabError as e:
                aqt.utils.showWarning(f"Mecab error: {e}")
                return None
            except ParsingError as e:
                aqt.utils.showWarning(f"Conversion failed. Error: {e}")
                return None

    _replace(edit, transform)


def inject_buttons(buttons: List[str], edit: Editor):
    buttons.append(edit.addButton(
        icon=get_path("assets", "convert.svg"),
        cmd="jrp_generate_default",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.DEFAULT),
        tip="(Re)generate readings and accents with default syntax (F2)",
        keys="F2")
    )
    buttons.append(edit.addButton(
        icon=get_path("assets", "migaku.svg"),
        cmd="jrp_generate_migaku",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.MIGAKU),
        tip="(Re)generate readings and accents with Migaku syntax (Ctrl+F2)",
        keys="Ctrl+F2")
    )
    buttons.append(edit.addButton(
        icon=get_path("assets", "restore.svg"),
        cmd="jrp_remove",
        func=lambda e: _convert(e, ConversionType.REMOVE),
        tip="Restore original text (F4)",
        keys="F4")
    )
