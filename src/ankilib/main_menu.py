import aqt
from PyQt5.QtWidgets import QAction

from .prefs_ui import show_ui


def insert_menu_items():
    tools_menu = aqt.mw.form.menuTools
    action = QAction("&Japanese Reading/Accent preferences", tools_menu)
    action.triggered.connect(lambda _: show_ui())
    tools_menu.addAction(action)
