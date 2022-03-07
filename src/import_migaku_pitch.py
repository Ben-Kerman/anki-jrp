#!/bin/python
# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import json
import lzma
import re
import sys
from dataclasses import dataclass

from pylib.accents import Accent
from pylib.dictionary import AccentEntry
from pylib.normalize import split_moras, to_hiragana
from pylib.util import warn


@dataclass
class ImportEntry(AccentEntry):
    sources: list[str]

    def __init__(self, reading: str, variant: str, accents: list[Accent], source: str):
        super().__init__(to_hiragana(reading), [variant], accents)
        if source == "nhk":
            self.sources = ["日"]
        elif source == "daiji":
            self.sources = ["林"]
        elif source == "mia":
            self.sources = ["Ｍ"]
        elif source == "wa":
            self.sources = ["和"]
        elif source == "shin":
            self.sources = ["新"]
        else:
            self.sources = []
            warn(f"unknown source: {source}")

    def fmt_line(self) -> str:
        return f"{self.reading}\t" \
               f"{','.join(self.variants)}\t" \
               f"{','.join(map(str, self.accents))}\t" \
               f"{''.join(self.sources)}\n"


fix_re = re.compile(r"[⁎⁑∘。]")


def fix_src_entry(src_entry: list) -> list | None:
    if "…" in src_entry[1]:
        return None
    src_entry[0] = fix_re.sub("", src_entry[0])
    src_entry[1] = fix_re.sub("", src_entry[1])
    return src_entry


def convert_accents(src_entry: list) -> list[Accent]:
    def convert(acc_nums: list[int], nhk_reading: str | None = None) -> Accent | None:
        if len(acc_nums) < 1:
            warn(f"zero length accent list: {src_entry[0]}")
            return None
        elif len(acc_nums) == 1:
            return Accent(acc_nums[0])
        else:
            if not nhk_reading:
                warn(f"missing NHK reading for split accent: {src_entry[0]}; {acc_nums}")
                return None

            part_readings = nhk_reading.replace(chr(0x309a), "").split("・")
            if len(part_readings) != len(acc_nums):
                warn(f"invalid number of parts: {src_entry[0]}; {acc_nums}; {nhk_reading}")
                return None

            parts: list[tuple[int, int]] = []
            for acc_num, reading in zip(acc_nums, part_readings):
                moras = split_moras(reading)
                parts.append((acc_num, len(moras)))

            return Accent(parts)

    if src_entry[4]:
        itr = (convert(nums, rdng[0]) for nums, rdng in zip(src_entry[5], src_entry[4]))
    else:
        itr = (convert(nums) for nums in src_entry[5])

    return [a for a in itr if a]


entries: list[ImportEntry] = []
readings: dict[str, list[ImportEntry]] = {}
sources: set[str] = set()

for src_path in sys.argv[2:]:
    with open(src_path, encoding="utf-8") as sfd:
        src_dict = json.load(sfd)

    for src_entry in src_dict:
        src_entry = fix_src_entry(src_entry)
        if not src_entry:
            continue

        if "," in src_entry[0]:
            warn(f"skipping variant containing comma: {src_entry[0]}")
            continue

        sources.add(src_entry[7])
        accents = convert_accents(src_entry)
        if not accents:
            warn(f"empty accent list, skipping: {src_entry[0]}")
            continue

        entry = ImportEntry(src_entry[1], src_entry[0], accents, src_entry[7])
        same_reading = readings.setdefault(entry.reading, [])
        if same_accent := next((e for e in same_reading if set(entry.accents) == set(e.accents)), None):
            if entry.variants[0] not in same_accent.variants:
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

warn("sources:", sources)
