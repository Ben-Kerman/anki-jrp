import os.path
from lzma import LZMAError
from typing import Type, TypeVar

import aqt
from aqt.operations import QueryOp

from .util import get_path
from ..pylib.dictionary import AccentEntry, BasicDict, Dictionary, VariantEntry
from ..pylib.preferences import Prefs

T = TypeVar("T")

_prefs_path = get_path("user_files", "config.json")


def load_prefs():
    if os.path.exists(_prefs_path):
        return Prefs.load_from_file(_prefs_path)
    else:
        return Prefs()


def save_prefs():
    prefs.write_to_file(_prefs_path)


def load_dict():
    def load_data(desc: str, filename: str, entry_t: Type[T]) -> BasicDict[T]:
        path = get_path("user_files", "data", filename)
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


prefs = load_prefs()
dictionary: Dictionary | None = None

QueryOp(parent=aqt.mw, op=lambda col: load_dict(), success=lambda _: print("JRP data loaded")).run_in_background()
