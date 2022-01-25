from typing import Callable

from aqt import editor, gui_hooks

_trans = {
    "\r": "\\r",
    "\n": "\\n",
    "\"": "\\\"",
    "\\": "\\\\",
}


def _escape_js_str(val: str) -> str:
    return "".join([_trans[c] if c in _trans else c for c in val])


def _replace(edit: editor.Editor, transform: Callable[[str], str]):
    def inject_html(new_html: str):
        nonlocal edit
        edit.web.page().runJavaScript(f"""
        editable = getCurrentField().activeInput
        editable.fieldHTML = \"{_escape_js_str(transform(new_html))}\"
        editable.caretToEnd()""")

    edit.web.page().runJavaScript("getCurrentField().activeInput.fieldHTML", lambda html: inject_html(html))


def _inject_shortcuts(shortcuts: list[tuple], edit: editor.Editor):
    shortcuts.append(("F2", lambda: _replace(edit, lambda h: f"〜{h}〜")))


gui_hooks.editor_did_init_shortcuts.append(_inject_shortcuts)
