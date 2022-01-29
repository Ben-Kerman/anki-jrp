#!/bin/python

import gzip
import lzma
import sys
import xml.etree.ElementTree

with gzip.open(sys.argv[2], "rt", encoding="utf-8") as sfd:
    jmd_root = xml.etree.ElementTree.parse(sfd).getroot()

with lzma.open(sys.argv[1], "wt", encoding="utf-8") as tfd:
    tfd.write("# kanji-reading mapping generated from JMdict\n")
    tfd.write("# format: word<TAB>reading\n")
    for entry in jmd_root:
        kebs = [r.find("keb").text for r in entry.findall("k_ele")]
        for reading in entry.findall("r_ele"):
            # TODO: don't add katakana reading if there's already equivalent hiragana
            reb = reading.find("reb").text
            restr = [rs.text for rs in reading.findall("re_restr")]
            for var in restr if len(restr) > 0 else kebs:
                tfd.write(f"{var}\t{reb}\n")
