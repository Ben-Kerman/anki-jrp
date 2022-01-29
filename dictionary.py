import lzma
import os
import sys
from typing import TextIO

from util import warn


class DictionaryException(Exception):
    pass


class Entry:
    word: str
    reading: str
    accents: list[int]
    source: str

    def __init__(self, word: str, reading: str, accents: list[int], source: str):
        self.word = sys.intern(word)
        self.reading = sys.intern(reading)
        self.accents = accents
        self.source = sys.intern(source)

    @classmethod
    def from_line(cls, line: str):
        vals = line.split("\t")
        if len(vals) != 4:
            raise ValueError
        accents = [int(acc) for acc in vals[2].split(",")]
        return cls(vals[0], vals[1], accents, vals[3])


class AccentDict:
    _entries: list[Entry]
    _word_idx: dict[str, list[Entry]]
    _rdng_idx: dict[str, list[Entry]]

    def __init__(self, path):
        self._entries = []
        self._word_idx = {}
        self._rdng_idx = {}

        fd: TextIO
        with lzma.open(path, "rt", encoding="utf-8") as fd:
            for line in (rl.strip() for rl in fd):
                if line.lstrip().startswith("#"):
                    continue

                try:
                    entry = Entry.from_line(line)
                    self._entries.append(entry)
                    self._word_idx.setdefault(entry.word, []).append(entry)
                    self._rdng_idx.setdefault(entry.reading, []).append(entry)
                except ValueError:
                    warn(f"skipping invalid dict entry: {line}")

    def look_up_word(self, word: str) -> list[Entry] | None:
        return self._word_idx.get(word)

    def look_up_reading(self, reading: str) -> list[Entry] | None:
        return self._rdng_idx.get(reading)


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
