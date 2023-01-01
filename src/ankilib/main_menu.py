# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import aqt
from aqt.qt import QAction

from .prefs_ui import show_ui


def insert_menu_items():
    tools_menu = aqt.mw.form.menuTools
    action = QAction("&JRP Add-on Preferences...", tools_menu)
    action.triggered.connect(lambda _: show_ui())
    tools_menu.addAction(action)
