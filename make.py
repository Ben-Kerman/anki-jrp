#!/bin/python
import json
import os
import shutil
import sys
from collections.abc import Sequence
from datetime import datetime
from zipfile import ZIP_LZMA, ZipFile, ZipInfo

if len(sys.argv) < 3:
    sys.exit("invalid number of arguments; usage: ./make.py <DATA DIR> <WINDOWS BIN DIR> [<IPADIC DIR>]")

_, data_dir, windows_bin_dir = sys.argv[:3]
ipadic_dir = sys.argv[3] if len(sys.argv) >= 4 else None

version_dict = {}
with open("src/pylib/version.py") as vfd:
    exec(vfd.read(), version_dict)
version = version_dict["script"]
addon_id = "japanese-readings-and-pitch-accent"
name = "Japanese Readings and Pitch Accent"
manifest = {"package": addon_id, "name": name}

if os.path.exists("target/"):
    shutil.rmtree("target/")
os.makedirs("target/", exist_ok=True)

now = datetime.timetuple(datetime.now())


def add_data(zf: ZipFile, data: bytes, tgt_path: str, compress: bool = True):
    zi = ZipInfo(tgt_path, date_time=now)
    if compress and len(data) > 100:
        zi.compress_type = ZIP_LZMA
    with zf.open(zi, "w") as zfd:
        zfd.write(data)


def add_file(zf: ZipFile, src_path: str, tgt_path: str, compress: bool = True):
    with open(src_path, "rb") as fd:
        add_data(zf, fd.read(), tgt_path, compress)


def add_files(zf: ZipFile, src_path: str, tgt_path: str | None = None, ext: Sequence[str] | None = None):
    for filename in os.listdir(src_path):
        path = os.path.join(src_path, filename)
        if os.path.isfile(path) and (not ext or os.path.splitext(filename)[1] in ext):
            zpath = os.path.join(tgt_path, filename) if tgt_path else filename
            add_file(zf, path, zpath)


def make_addon(path: str, full: bool, dic: bool = False):
    with ZipFile(path, "w") as azip:
        for dirname in ("pylib", "ankilib", "assets", "style"):
            add_files(azip, os.path.join("src", dirname), dirname, (".py", ".svg", ".css", ".pat", ".var"))
        add_files(azip, "src/ts", "js", (".js",))
        add_file(azip, "src/__init__.py", "__init__.py")
        add_data(azip, json.dumps(manifest).encode("utf-8"), "manifest.json")

        if full:
            add_file(azip, os.path.join(data_dir, "accents.xz"), "data/accents.xz", compress=False)
            add_file(azip, os.path.join(data_dir, "variants.xz"), "data/variants.xz", compress=False)

            add_file(azip, os.path.join(windows_bin_dir, "libmecab.dll"), "bin/libmecab.dll")
            add_file(azip, os.path.join(windows_bin_dir, "mecab.exe"), "bin/mecab.exe")
            add_data(azip, b"", "bin/mecabrc")

        if dic:
            add_files(azip, ipadic_dir, "data/ipadic")


make_addon(f"target/{addon_id}_{version}.ankiaddon", full=False)
make_addon(f"target/{addon_id}_{version}_full.ankiaddon", full=True)
if ipadic_dir:
    make_addon(f"target/{addon_id}_{version}_ipadic.ankiaddon", full=True, dic=True)

with ZipFile(f"target/{addon_id}_script-only_{version}.zip", "w") as szip:
    add_files(szip, "src/pylib", ext=(".py",))
