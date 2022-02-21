from collections.abc import Callable

from aqt import editor, gui_hooks

_js_esc = str.maketrans({
    "\r": "\\r",
    "\n": "\\n",
    "\"": "\\\"",
    "\\": "\\\\",
})


def _replace(edit: editor.Editor, transform: Callable[[str], str]):
    def inject_html(new_html: str):
        nonlocal edit
        edit.web.page().runJavaScript(f"""
        editable = getCurrentField().activeInput
        editable.fieldHTML = \"{transform(new_html).translate(_js_esc)}\"
        editable.caretToEnd()""")

    edit.web.page().runJavaScript("getCurrentField().activeInput.fieldHTML", lambda html: inject_html(html))


def _inject_shortcuts(shortcuts: list[tuple], edit: editor.Editor):
    shortcuts.append(("F2", lambda: _replace(edit, lambda h: f"〜{h}〜")))


gui_hooks.editor_did_init_shortcuts.append(_inject_shortcuts)
