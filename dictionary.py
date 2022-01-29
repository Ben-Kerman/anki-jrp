import lzma
import os
import sys
from typing import TextIO

from util import warn


class DictionaryException(Exception):
    pass


class AccentEntry:
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
    _entries: list[AccentEntry]
    _word_idx: dict[str, list[AccentEntry]]
    _rdng_idx: dict[str, list[AccentEntry]]

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
                    entry = AccentEntry.from_line(line)
                    self._entries.append(entry)
                    self._word_idx.setdefault(entry.word, []).append(entry)
                    self._rdng_idx.setdefault(entry.reading, []).append(entry)
                except ValueError:
                    warn(f"skipping invalid dict entry: {line}")

    def look_up_word(self, word: str) -> list[AccentEntry] | None:
        return self._word_idx.get(word)

    def look_up_reading(self, reading: str) -> list[AccentEntry] | None:
        return self._rdng_idx.get(reading)


class VariantEntry:
    reading: str
    variants: list[str]

    def __init__(self, reading: str, variants: list[str]):
        self.variants = [sys.intern(v) for v in variants]
        self.reading = sys.intern(reading)

    @classmethod
    def from_line(cls, line: str):
        vals = line.split("\t")
        if len(vals) != 2:
            raise ValueError
        return cls(vals[0], vals[1].split(","))


class VariantDict:
    _entries: list[VariantEntry]
    _readings: dict[str, list[VariantEntry]]
    _variants: dict[str, list[VariantEntry]]

    def __init__(self, dir):
        self._entries = []
        self._variants = {}
        self._readings = {}

        with os.scandir(dir) as itr:
            e: os.DirEntry
            for file in (e for e in itr if e.is_file() and os.path.basename(e.path).endswith(".dict.xz")):
                fd: TextIO
                with lzma.open(file.path, "rt", encoding="utf-8") as fd:
                    for line in (rl.rstrip("\r\n") for rl in fd):
                        if line.startswith("#"):
                            continue

                        try:
                            entry = VariantEntry.from_line(line)
                            self._entries.append(entry)
                            self._readings.setdefault(entry.reading, []).append(entry)
                            for var in entry.variants:
                                self._variants.setdefault(var, []).append(entry)
                        except ValueError:
                            warn(f"skipping invalid dict entry: {line}")

    def look_up_variant(self, val: str) -> list[VariantEntry] | None:
        return self._variants.get(val)

    def look_up_reading(self, val: str) -> list[VariantEntry] | None:
        return self._readings.get(val)
