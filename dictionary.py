import lzma
import os
import sys
from typing import Generic, TextIO, Type, TypeVar

from attr import dataclass

from util import warn

T = TypeVar("T")


class BasicDict(Generic[T]):
    _readings: dict[str, list[T]]
    _variants: dict[str, list[T]]

    def __init__(self, entry_type: Type[T], path):
        self.variants = {}
        self.readings = {}

        fd: TextIO
        with lzma.open(path, "rt", encoding="utf-8") as fd:
            for line in (rl.rstrip("\r\n") for rl in fd):
                if line.startswith("#"):
                    continue

                try:
                    entry = entry_type.from_line(line)
                    entry_type.dict_insert(self, entry)
                except ValueError:
                    warn(f"skipping invalid dict entry: {line}")

    def look_up_variant(self, val: str) -> list[T] | None:
        return self.variants.get(val)

    def look_up_reading(self, val: str) -> list[T] | None:
        return self.readings.get(val)


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

    @classmethod
    def dict_insert(cls, bdict, entry):
        bdict.variants.setdefault(entry.word, []).append(entry)
        bdict.readings.setdefault(entry.reading, []).append(entry)


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

    @classmethod
    def dict_insert(cls, bdict, entry):
        bdict.readings.setdefault(entry.reading, []).append(entry)
        for var in entry.variants:
            bdict.variants.setdefault(var, []).append(entry)


AccentDict = BasicDict[AccentEntry]
VariantDict = BasicDict[VariantEntry]


@dataclass(repr=False)
class LookupResult:
    reading: str
    accents: list[int] | None = None

    def __repr__(self):
        return f"R[{self.reading},{self.accents}]"


@dataclass(repr=False)
class Lookup:
    results: list[LookupResult]
    uncertain: bool = False

    def __repr__(self):
        return f"LU[{self.results}{';uncertain' if self.uncertain else ''}]"

    def has_accents(self):
        return all(r.accents for r in self.results)


class Dictionary:
    accent: AccentDict
    variant: VariantDict

    @classmethod
    def default_path(cls) -> str:
        return os.path.join(os.path.dirname(__file__), "user_data")

    def __init__(self, adict: AccentDict | None = None, vdict: VariantDict | None = None):
        self.accent = adict or BasicDict(AccentEntry, os.path.join(type(self).default_path(), "accents.xz"))
        self.variant = vdict or BasicDict(VariantEntry, os.path.join(type(self).default_path(), "variants.xz"))

    def _find_from_var(self, ve: VariantEntry, reading: str | None = None) -> Lookup | None:
        rdng = reading or ve.reading
        for var in ve.variants:
            acc_lookup = self.accent.look_up_variant(var)
            if acc_lookup is not None:
                acc_res = next((e for e in acc_lookup if e.reading == rdng), None)
                if acc_res is not None:
                    return Lookup([LookupResult(rdng, acc_res.accents)])
        return None

    def look_up(self, word: str, candidate_reading: str | None = None) -> Lookup | None:
        by_word = self.accent.look_up_variant(word)
        if by_word is not None:
            ent = next((e for e in by_word if e.reading == candidate_reading), None)
            if ent is not None:
                return Lookup([LookupResult(ent.reading, ent.accents)])
            else:
                return Lookup([LookupResult(by_word[0].reading, by_word[0].accents)])

        if candidate_reading is not None:
            by_reading = self.accent.look_up_reading(candidate_reading)
            if by_reading is not None and len(by_reading) == 1:
                return Lookup([LookupResult(by_reading[0].reading, by_reading[0].accents)])

        vars_by_word = self.variant.look_up_variant(word)
        if vars_by_word is not None:
            vars_with_cr = [e for e in vars_by_word if e.reading == candidate_reading]
            vars = vars_with_cr if len(vars_with_cr) > 0 else vars_by_word
            for var in vars:
                if (res := self._find_from_var(var)) is not None:
                    return res
            return Lookup([LookupResult(vars[0].reading)])

        if candidate_reading is not None:
            vars_by_reading = self.variant.look_up_reading(candidate_reading)
            if vars_by_reading is not None and len(vars_by_reading) == 1:
                if (res := self._find_from_var(vars_by_reading[0], candidate_reading)) is not None:
                    return res

        return None
