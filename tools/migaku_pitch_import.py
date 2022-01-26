#!/bin/python

import json
import lzma
import sys


class Entry:
    word: str
    reading: str
    accents: [int]
    source: str

    def __init__(self, word: str, reading: str, accents: [[int]], source: str):
        self.word = word
        self.reading = reading
        self.accents = [a for inner in accents for a in inner]
        match source:
            case "nhk":
                self.source = "日"
            case "daiji":
                self.source = "林"
            case "mia":
                self.source = "Ｍ"
            case "wa":
                self.source = "和"
            case "shin":
                self.source = "新"

    def fmt_line(self):
        return f"{self.word}\t{self.reading}\t{','.join(map(str, self.accents))}\t{self.source}\n"


entries = []
sources = set()

for src_path in sys.argv[2:]:
    with open(src_path, encoding="utf-8") as sfd:
        src_dict = json.load(sfd)

    for src_entry in src_dict:
        sources.add(src_entry[7])
        entries.append(Entry(src_entry[0], src_entry[1], src_entry[5], src_entry[7]))

with lzma.open(sys.argv[1], "wt", encoding="utf-8") as tfd:
    tfd.write("# compiled pitch accent dictionary by Yoga, taken from the Migaku Japanese addon\n")
    tfd.write("# sources: 日: NHKアクセント 1998版; 林: 大辞林 第二版; Ｍ: manual changes from MIA; 和: 和独辞典; 新: 新明解 第五版\n")
    tfd.write("# format: word<TAB>reading<TAB>accent{,accent}<TAB>source\n")
    for entry in entries:
        tfd.write(entry.fmt_line())

print(sources, file=sys.stderr)
