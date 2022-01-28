import lzma
import os
import sys
from typing import TextIO

from util import warn


class ReadingDict:
    _variants: dict[str, list[str]]

    def __init__(self, dir):
        self._variants = {}

        with os.scandir(dir) as itr:
            e: os.DirEntry
            for file in (e for e in itr if e.is_file() and os.path.basename(e.path).endswith(".dict.xz")):
                fd: TextIO
                with lzma.open(file.path, "rt", encoding="utf-8") as fd:
                    for line in (rl.rstrip("\r\n") for rl in fd):
                        if line.startswith("#"):
                            continue

                        try:
                            variant, reading = [sys.intern(s) for s in line.split("\t")]
                            if variant not in self._variants:
                                self._variants[variant] = [reading]
                            elif reading not in self._variants[variant]:
                                self._variants[variant].append(reading)
                        except ValueError:
                            warn(f"skipping invalid dict entry: {line}")

    def look_up(self, val: str):
        return self._variants[val]
