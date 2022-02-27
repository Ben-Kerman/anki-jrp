import os.path
import shutil
from os.path import dirname, join

from anki.collection import Collection

_filenames = ("jrp-downstep-dark.svg", "jrp-downstep-dark-vert.svg",
              "jrp-downstep-light.svg", "jrp-downstep-light-vert.svg")


def path_for_asset(filename: str) -> str:
    return join(dirname(dirname(__file__)), "assets", filename)


def copy_assets(col: Collection):
    cm_dir = col.media.dir()
    for fn in _filenames:
        asset_file_path = path_for_asset(fn)
        cm_file_path = join(cm_dir, f"_{fn}")
        if os.path.exists(cm_file_path):
            with open(asset_file_path) as afd, open(cm_file_path) as cfd:
                if afd.read() == cfd.read():
                    continue
        shutil.copy2(asset_file_path, cm_file_path)
