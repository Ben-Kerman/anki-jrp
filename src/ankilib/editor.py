import re
from collections.abc import Callable, Generator
from enum import Enum, auto

import aqt.utils
from aqt.editor import Editor

from . import global_vars as gv
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import MecabError
from ..pylib.output import OutputType, fmt_jrp, fmt_migaku
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


_nl_re = re.compile(r"[^\S\r\n]*[\r\n]+[^\S\r\n]*")

_brace_re = re.compile(r"[^\\]{")
_tag_re = re.compile(r"[^\\]\[(.+?)[^\\]]")


def detect_syntax(val: str) -> OutputType | None:
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


def _convert(edit: Editor, conv_type: ConversionType, out_type: OutputType | None = None):
    def gen_lines(val: str) -> Generator[str]:
        lines = strip_html(val)
        if t := detect_syntax(val):
            parser = parse_migaku if t == OutputType.MIGAKU else parse_jrp
            yield from ("".join(u.text() for u in parser(line)) for line in lines)
        else:
            yield from lines

    def transform(val: str) -> str | None:
        val = _nl_re.sub(" ", val)
        if conv_type == ConversionType.REMOVE:
            return "<br>".join(gen_lines(val))
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


def inject_buttons(buttons: list[str], edit: Editor):
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_generate_default",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.DEFAULT),
        tip="(Re)generate readings and accents with default syntax (F2)",
        keys="F2")
    )
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_generate_migaku",
        func=lambda e: _convert(e, ConversionType.GENERATE, OutputType.MIGAKU),
        tip="(Re)generate readings and accents with Migaku syntax (Ctrl+F2)",
        keys="Ctrl+F2")
    )
    buttons.append(edit.addButton(
        icon=None,
        cmd="jrp_remove",
        func=lambda e: _convert(e, ConversionType.REMOVE),
        tip="Restore original text (F4)",
        keys="F4")
    )
