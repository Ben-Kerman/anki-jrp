#!/bin/python
# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import gzip
import lzma
import sys
import xml.etree.ElementTree

from pylib.normalize import itr_to_hira, to_hiragana

with gzip.open(sys.argv[2], "rt", encoding="utf-8") as sfd:
    jmd_root = xml.etree.ElementTree.parse(sfd).getroot()

with lzma.open(sys.argv[1], "wt", encoding="utf-8") as tfd:
    tfd.write("# word variant mapping generated from JMdict\n")
    tfd.write("# format: reading{,reading}<TAB>variant{,variant}\n")
    for entry in jmd_root:
        k_eles = entry.findall("k_ele")
        if not k_eles:
            continue

        equiv_readings = {}
        for reading in entry.findall("r_ele"):
            reb_hira = to_hiragana(reading.find("reb").text)
            restr = [rs.text for rs in reading.findall("re_restr")]
            equiv_readings.setdefault(reb_hira, []).append(restr)
            # TODO: don't add katakana reading if there's already equivalent hiragana

        for reading, restrs in equiv_readings.items():
            non_empty = [r for r in restrs if len(r) > 0]
            if len(non_empty) > 0:
                s = (set(r) for r in non_empty)
                first = next(s)
                if not all(r == first for r in s):
                    variants = itr_to_hira(r for ne in non_empty for r in ne)
                else:
                    variants = itr_to_hira(non_empty[0])
            else:
                variants = itr_to_hira(r.find("keb").text for r in k_eles)
            tfd.write(f"{reading}\t{','.join(variants)}\n")
