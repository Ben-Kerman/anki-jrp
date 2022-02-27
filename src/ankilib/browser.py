from typing import Sequence

from PyQt5.QtWidgets import QAction, QMenu
from anki.notes import NoteId
from aqt.browser import Browser


def change_syntax(n_ids: Sequence[NoteId]):
    print(n_ids)  # TODO


def insert_menu_items(brws: Browser):
    note_menu = brws.form.menu_Notes
    note_menu.addSeparator()
    addon_menu = QMenu("&Japanese Readings && Accent Add-on", note_menu)

    syn_conv_action = QAction("&Change Syntax", addon_menu)
    syn_conv_action.triggered.connect(lambda _: change_syntax(brws.selected_notes()))

    addon_menu.addAction(syn_conv_action)
    note_menu.addMenu(addon_menu)
