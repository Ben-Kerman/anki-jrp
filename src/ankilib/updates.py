# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import os.path
import platform
import shutil
from typing import Optional

from anki.collection import Collection

from . import global_vars
from .templates import update_all_note_types
from .util import copy_assets, get_path
from ..pylib import version


def _path() -> str:
    uf_path = get_path("user_files")
    if not os.path.exists(uf_path):
        os.makedirs(uf_path)

    return os.path.join(uf_path, "last-version")


def _col_path(col: Collection) -> str:
    return os.path.join(os.path.dirname(col.path), "jrp-last-version")


def check_update(col: Optional[Collection] = None) -> bool:
    path = _col_path(col) if col else _path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fd:
            return fd.read().strip() != version.script
    return True


def update() -> None:
    if not check_update():
        return

    with open(_path(), "w", encoding="utf-8") as fd:
        fd.write(version.script)

    bin_path = get_path("bin")
    if platform.system() != "Windows" and os.path.exists(bin_path):
        shutil.rmtree(bin_path)


def update_collection(col: Collection) -> None:
    if not check_update(col):
        return

    copy_assets(col)
    update_all_note_types(col, global_vars.prefs.addon)
    with open(_col_path(col), "w", encoding="utf-8") as fd:
        fd.write(version.script)
