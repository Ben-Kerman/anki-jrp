# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import os.path
from lzma import LZMAError
from os.path import dirname
from typing import Optional, Type, TypeVar

import aqt
from anki.collection import Collection
from aqt.operations import QueryOp

from .templates import update_all_note_types
from .util import get_path
from ..pylib.dictionary import AccentEntry, BasicDict, Dictionary, VariantEntry
from ..pylib.mecab import Mecab
from ..pylib.preferences import Prefs
from ..pylib.util import ConfigError

T = TypeVar("T")


def _prefs_path(col: Collection) -> str:
    return os.path.join(dirname(col.path), "jrp-config.json")


def load_prefs(col: Collection) -> None:
    loaded_prefs = None
    if os.path.exists(_prefs_path(col)):
        load_res = Prefs.load_from_file(_prefs_path(col))
        if isinstance(load_res, ConfigError):
            aqt.utils.showWarning(f"Failed to load config, falling back on defaults.\n"
                                  f"Error: {load_res.msg}")
        elif load_res:
            loaded_prefs = load_res

    update_prefs(loaded_prefs or Prefs())


def update_prefs(new_prefs: Prefs):
    global prefs
    update_all_note_types(aqt.mw.col, new_prefs.addon, prefs and prefs.addon)
    prefs = new_prefs
    init_mecab()


def save_prefs():
    if prefs is None:
        return

    try:
        prefs.write_to_file(_prefs_path(aqt.mw.col))
    except Exception as e:
        aqt.utils.showWarning(f"Failed to update config file.\nError: {e}")


def init_mecab():
    global mecab_handle
    exe_path = None if prefs.addon.mecab_use_system_exe else get_path(prefs.addon.mecab_path)
    dir_path = None if prefs.addon.mecab_use_system_dict else get_path(prefs.addon.mecab_dict_dir)
    mecab_handle = Mecab(exe_path, dir_path)


def load_dict():
    def load_data(desc: str, filename: str, entry_t: Type[T]) -> BasicDict[T]:
        path = get_path("data", filename)
        if not os.path.exists(path):
            aqt.mw.taskman.run_on_main(
                lambda: aqt.utils.showWarning(
                    f"No {desc} data at {path}, reading/accent generation will not work.",
                    title="Japanese Reading and Pitch Accent Add-on Warning"
                )
            )
        else:
            try:
                return BasicDict(entry_t, path)
            except (OSError, LZMAError) as e:
                aqt.mw.taskman.run_on_main(
                    lambda: aqt.utils.showWarning(
                        f"Loading {path} failed, reading/accent generation will not work:\n{e}",
                        title="Japanese Reading and Pitch Accent Add-on Warning"
                    )
                )

    acc_dic = load_data("accent", "accents.xz", AccentEntry)
    var_dic = load_data("variants", "variants.xz", VariantEntry)
    if acc_dic and var_dic:
        global dictionary
        dictionary = Dictionary(acc_dic, var_dic)


prefs: Optional[Prefs] = None
mecab_handle: Optional[Mecab] = None
dictionary: Optional[Dictionary] = None

QueryOp(parent=aqt.mw, op=lambda col: load_dict(), success=lambda _: print("JRP data loaded")).run_in_background()


def convert_check() -> bool:
    if not dictionary:
        aqt.utils.showWarning("Dictionary is not (yet) loaded, can't convert.")
        return False
    return True
