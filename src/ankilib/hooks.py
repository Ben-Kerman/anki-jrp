import aqt

from . import browser, editor, global_vars, main_menu, updates

updates.update()

aqt.gui_hooks.collection_did_load.append(global_vars.load_prefs)
aqt.gui_hooks.collection_did_load.append(updates.update_collection)
aqt.gui_hooks.main_window_did_init.append(main_menu.insert_menu_items)
aqt.gui_hooks.editor_did_init_buttons.append(editor.inject_buttons)
aqt.gui_hooks.browser_menus_did_init.append(browser.insert_menu_items)
