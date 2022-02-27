import aqt

from . import editor

aqt.gui_hooks.editor_did_init_buttons.append(editor.inject_buttons)
