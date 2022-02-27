import aqt

from . import browser, editor, main_menu

aqt.gui_hooks.main_window_did_init.append(main_menu.insert_menu_items)
aqt.gui_hooks.editor_did_init_buttons.append(editor.inject_buttons)
aqt.gui_hooks.browser_menus_did_init.append(browser.insert_menu_items)
