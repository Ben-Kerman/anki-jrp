# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import os.path
import shutil
from os.path import dirname, join

from anki.collection import Collection

_filenames = ("jrp-downstep-dark.svg", "jrp-downstep-dark-vert.svg",
              "jrp-downstep-light.svg", "jrp-downstep-light-vert.svg")


def get_path(*comps: str) -> str:
    addon_dir = dirname(dirname(__file__))
    if not comps:
        return addon_dir
    else:
        return join(addon_dir, *comps)


def get_asset_path(filename: str) -> str:
    return get_path("assets", filename)


def copy_assets(col: Collection):
    cm_dir = col.media.dir()
    for fn in _filenames:
        asset_file_path = get_asset_path(fn)
        cm_file_path = join(cm_dir, f"_{fn}")
        if os.path.exists(cm_file_path):
            with open(asset_file_path, "rb") as afd, open(cm_file_path, "rb") as cfd:
                if afd.read() == cfd.read():
                    continue
        shutil.copy2(asset_file_path, cm_file_path)
