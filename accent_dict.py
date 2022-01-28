import lzma
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
    _word_idx: dict[str, Entry]
    _rdng_idx: dict[str, Entry]

    def __init__(self, path):
        def get_index(idx: dict, key: str) -> list[Entry]:
            if key not in idx:
                idx[key] = []
            return idx[key]

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
                    get_index(self._word_idx, entry.word).append(entry)
                    get_index(self._rdng_idx, entry.reading).append(entry)
                except ValueError:
                    warn(f"skipping invalid dict entry: {line}")

    def look_up_word(self, word: str) -> list[Entry] | None:
        return self._word_idx.get(word)

    def look_up_reading(self, reading: str) -> list[Entry] | None:
        return self._rdng_idx.get(reading)
