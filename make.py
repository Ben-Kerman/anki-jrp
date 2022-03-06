#!/bin/python

import os
import shutil
from collections.abc import Sequence
from datetime import datetime
from zipfile import ZIP_LZMA, ZipFile, ZipInfo

version_dict = {}
with open("src/pylib/version.py") as vfd:
    exec(vfd.read(), version_dict)
name = "japanese-readings-and-pitch-accent"
version = version_dict["script"]

if os.path.exists("target/"):
    shutil.rmtree("target/")
os.makedirs("target/", exist_ok=True)

now = datetime.timetuple(datetime.now())


def add_file(zf: ZipFile, src_path: str, tgt_path: str, compress: bool = True):
    zi = ZipInfo(tgt_path, date_time=now)
    if compress and os.path.getsize(src_path) > 100:
        zi.compress_type = ZIP_LZMA
    with open(src_path, "rb") as fd, zf.open(zi, "w") as zfd:
        zfd.write(fd.read())


def add_files(zf: ZipFile, src_path: str, tgt_path: str | None = None, ext: Sequence[str] | None = None):
    for filename in os.listdir(src_path):
        path = os.path.join(src_path, filename)
        if os.path.isfile(path) and (not ext or os.path.splitext(filename)[1] in ext):
            zpath = os.path.join(tgt_path, filename) if tgt_path else filename
            add_file(zf, path, zpath)


def make_addon(path: str, full: bool):
    with ZipFile(path, "w") as azip:
        for dirname in ("pylib", "ankilib", "assets", "style"):
            add_files(azip, os.path.join("src", dirname), dirname, (".py", ".svg", ".css", ".pat", ".var"))
        add_files(azip, "src/ts", "js", (".js",))
        add_file(azip, "src/__init__.py", "__init__.py")


make_addon(f"target/{name}_{version}.ankiaddon", full=False)
make_addon(f"target/{name}_{version}_full.ankiaddon", full=True)

with ZipFile(f"target/{name}_script-only_{version}.zip", "w") as szip:
    add_files(szip, "src/pylib", ext=(".py",))
