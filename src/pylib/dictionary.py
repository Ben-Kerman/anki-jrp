import lzma
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TextIO, Type, TypeVar

from .accents import Accent
from .normalize import is_kana, to_hiragana

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
                    print(f"skipping invalid dict entry: {line}")

    def look_up_variant(self, val: str) -> list[T] | None:
        return self.variants.get(val)

    def look_up_reading(self, val: str) -> list[T] | None:
        return self.readings.get(to_hiragana(val))


class AccentEntry:
    reading: str
    variants: list[str]
    accents: list[Accent]

    def __init__(self, reading: str, variants: list[str], accents: list[Accent]):
        self.reading = sys.intern(reading)
        self.variants = [sys.intern(v) for v in variants]
        self.accents = accents

    @classmethod
    def from_line(cls, line: str) -> "AccentEntry":
        vals = line.split("\t")
        if len(vals) != 4:
            raise ValueError
        accents = [Accent.from_str(acc_str) for acc_str in vals[2].split(",")]
        return cls(vals[0], vals[1].split(","), accents)

    @classmethod
    def dict_insert(cls, bdict, entry):
        bdict.readings.setdefault(entry.reading, []).append(entry)
        for var in entry.variants:
            bdict.variants.setdefault(var, []).append(entry)


class VariantEntry:
    reading: str
    variants: list[str]

    def __init__(self, reading: str, variants: list[str]):
        self.variants = [sys.intern(v) for v in variants]
        self.reading = sys.intern(reading)

    @classmethod
    def from_line(cls, line: str) -> "VariantEntry":
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
Entry = TypeVar("Entry", AccentEntry, VariantEntry)


@dataclass
class LookupResult:
    reading: str
    accents: list[Accent] | None = None

    def __repr__(self):
        return f"R[{self.reading},{self.accents}]"

    @classmethod
    def convert_entries(cls, entries: Iterable[Entry]) -> list["LookupResult"]:
        return [cls(e.reading, e.accents if isinstance(e, AccentEntry) else None) for e in entries]


@dataclass
class Lookup:
    results: list[LookupResult]
    uncertain: bool = False

    def __repr__(self):
        return f"LU[{self.results}{';uncertain' if self.uncertain else ''}]"

    def has_accents(self):
        return all(r.accents for r in self.results)


@dataclass
class Dictionary:
    accent: AccentDict
    variant: VariantDict

    def _variant_lookup(self, word: str, as_reading: bool = False) -> list[AccentEntry] | None:
        lu_fn = self.variant.look_up_reading if as_reading else self.variant.look_up_variant
        res = []
        var_ents = lu_fn(word)
        if not var_ents:
            return None
        for var in (var for ve in var_ents for var in ve.variants):
            acc_ents = self.accent.look_up_variant(var)
            if acc_ents:
                res.extend(acc_ent for acc_ent in acc_ents if acc_ent not in res)
        return res

    def look_up(self, word: str, reading_guess: str | None = None) -> Lookup | None:
        def filter_for_guess(entries: list[Entry], guess: str | None) -> list[Entry] | None:
            if not guess:
                return None
            return [e for e in entries if to_hiragana(e.reading) == to_hiragana(guess)]

        def check_uncertain(entrs: list[AccentEntry]) -> bool:
            return any(e.reading == entrs[0].reading for e in entrs[1:])

        word_direct_aent = self.accent.look_up_variant(word)
        if word_direct_aent:
            filtered_aent = filter_for_guess(word_direct_aent, reading_guess) or word_direct_aent
            return Lookup(LookupResult.convert_entries(filtered_aent), check_uncertain(filtered_aent))

        word_var_aent = self._variant_lookup(word)
        if word_var_aent:
            filtered_aent = filter_for_guess(word_var_aent, reading_guess) or word_var_aent
            return Lookup(LookupResult.convert_entries(filtered_aent), check_uncertain(filtered_aent))

        current_lu: Lookup | None = None
        read_direct_aent = self.accent.look_up_reading(word)
        if read_direct_aent:
            current_lu = Lookup(LookupResult.convert_entries(read_direct_aent), len(read_direct_aent) > 1)
            if not current_lu.uncertain:
                return current_lu

        read_var_aent = self._variant_lookup(word, as_reading=True)
        if read_var_aent:
            current_lu = Lookup(LookupResult.convert_entries(read_var_aent), len(read_var_aent) > 1)
            if not current_lu.uncertain:
                return current_lu

        if current_lu:
            return current_lu

        if not is_kana(word):
            word_direct_vent = self.variant.look_up_variant(word)
            if word_direct_vent:
                return Lookup(LookupResult.convert_entries(word_direct_vent))

        return current_lu
