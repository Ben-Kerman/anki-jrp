#!/bin/python

import json
import lzma
import sys

from pylib.normalize import to_hiragana
from pylib.util import warn


class Entry:
    reading: str
    variants: list[str]
    accents: list[int]
    sources: list[str]

    def __init__(self, reading: str, variant: str, accents: list[list[int]], source: str):
        self.reading = to_hiragana(reading)
        self.variants = [variant]
        self.accents = [a for inner in accents for a in inner]
        match source:
            case "nhk":
                self.sources = ["日"]
            case "daiji":
                self.sources = ["林"]
            case "mia":
                self.sources = ["Ｍ"]
            case "wa":
                self.sources = ["和"]
            case "shin":
                self.sources = ["新"]
            case _:
                warn(f"unknown source: {source}")

    def fmt_line(self):
        return f"{self.reading}\t" \
               f"{','.join(self.variants)}\t" \
               f"{','.join(map(str, self.accents))}\t" \
               f"{''.join(self.sources)}\n"


entries: list[Entry] = []
readings: dict[str, list[Entry]] = {}
sources: set[str] = set()

for src_path in sys.argv[2:]:
    with open(src_path, encoding="utf-8") as sfd:
        src_dict = json.load(sfd)

    for src_entry in src_dict:
        if "," in src_entry[0]:
            warn(f"skipping variant containing comma: {src_entry[0]}")
            continue

        sources.add(src_entry[7])
        entry = Entry(src_entry[1], src_entry[0], src_entry[5], src_entry[7])
        same_reading = readings.setdefault(entry.reading, [])
        if same_accent := next((e for e in same_reading if set(entry.accents) == set(e.accents)), None):
            if entry.variants not in same_accent.variants:
                same_accent.variants.extend(entry.variants)
                same_accent.variants.sort()
            same_accent.sources.extend(set(entry.sources) - set(same_accent.sources))
            same_accent.sources.sort()
        else:
            entries.append(entry)
            same_reading.append(entry)

entries.sort(key=lambda e: e.reading)

with lzma.open(sys.argv[1], "wt", encoding="utf-8") as tfd:
    tfd.write("# compiled pitch accent dictionary by Yoga, taken from the Migaku Japanese addon\n")
    tfd.write("# sources: 日: NHKアクセント 1998版; 林: 大辞林 第二版; Ｍ: manual changes from MIA; 和: 和独辞典; 新: 新明解 第五版\n")
    tfd.write("# format: reading<TAB>variant{,variant}<TAB>accent{,accent}<TAB>source{,source}\n")
    for entry in entries:
        tfd.write(entry.fmt_line())

print("sources:", sources, file=sys.stderr)
