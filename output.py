from collections.abc import Generator

from normalize import is_kana, to_katakana
from segments import Unit


class OutputError(Exception):
    pass


def _add_accent(unit: Unit) -> bool:
    if not unit.accents:
        return False

    if len(unit.segments) == 1:
        txt = unit.segments[0].text
        if is_kana(txt) and len(txt) < 3 and not unit.base_form:
            return False
    return True


_i_dan = ("キ", "ギ", "シ", "ジ", "チ", "ヂ", "ニ", "ヒ", "ビ", "ピ", "ミ", "リ")
_e_comp = ("イ", "ウ", "キ", "ギ", "ク", "グ", "シ", "ジ", "チ", "ツ", "ニ", "ヒ", "ビ", "ピ", "フ", "ミ", "リ", "ヴ")


def _split_moras(reading: str) -> list[str]:
    kana = to_katakana(reading)
    moras = []
    i = 0
    while i < len(kana):
        ck = kana[i]
        nk = kana[i + 1] if i + 1 < len(kana) else None
        if nk:
            if ck in _i_dan and nk in ("ャ", "ュ", "ョ") \
                    or nk == "ヮ" and ck in ("ク", "グ") \
                    or nk == "ァ" and ck in ("ツ", "フ", "ヴ") \
                    or nk == "ィ" and ck in ("ク", "グ", "ス", "ズ", "テ", "ツ", "デ", "フ", "イ", "ウ", "ヴ") \
                    or nk == "ゥ" and ck in ("ト", "ド", "ホ", "ウ") \
                    or nk == "ェ" and ck in _e_comp \
                    or nk == "ォ" and ck in ("ク", "グ", "ツ", "フ", "ウ", "ヴ") \
                    or nk == "ャ" and ck in ("フ", "ヴ") \
                    or nk == "ュ" and ck in ("テ", "デ", "フ", "ウ", "ヴ") \
                    or nk == "ョ" and ck in ("フ", "ヴ"):
                moras.append(ck + nk)
                i += 2
                continue
        moras.append(ck)
        i += 1
    return moras


def fmt_migaku(units: list[Unit]) -> str:
    def migaku_accents(unit: Unit) -> Generator[str]:
        moras = _split_moras(unit.reading())
        for acc in unit.accents:
            if acc == 0:
                yield "h"
            elif unit.base_form:
                yield f"k{acc}"
            elif acc == 1:
                yield "a"
            elif acc == len(moras):
                yield "o"
            else:
                yield f"n{acc}"

    def fmt_unit(unit: Unit) -> str:
        if len(unit.segments) == 1 and all(c == " " for c in unit.segments[0].text):
            return chr(0x2002)  # en space

        tag_content = ""
        if _add_accent(unit):
            if unit.base_form:
                tag_content += "," + unit.base_form
            tag_content += ";" + ",".join(migaku_accents(unit))

        if len(unit.segments) == 1 and (is_kana(unit.segments[0].text) or not unit.segments[0].reading):
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{unit.segments[0].text}{tag}"
        elif len(unit.segments) > 1 and is_kana(unit.segments[-1].text):
            tag_content = unit.reading(-1) + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            tail = unit.segments[-1].text
            return f"{unit.text(-1)}{tag}{tail}"
        else:
            tag_content = unit.reading() + tag_content
            tag = f"[{tag_content}]" if tag_content else ""
            return f"{unit.text()}{tag}"

    return " ".join(map(fmt_unit, units))


def fmt_jrp(units: list[Unit]) -> str:
    def fmt_unit(unit: Unit) -> str:
        def accent_strs(unit: Unit) -> Generator[str]:
            if unit.base_form:
                moras = len(_split_moras(unit.base_form))
                for acc in unit.accents:
                    yield str(acc - moras - 1) if acc != 0 else "0"
            else:
                for acc in unit.accents:
                    yield str(acc)

        def segment_strs(unit: Unit, add_accent: bool) -> Generator[str]:
            base = to_katakana(unit.base_form) if unit.base_form else None
            base_idx = 0
            use_special_base = False
            for i, s in enumerate(unit.segments):
                if add_accent and not use_special_base and base:
                    for k, c in enumerate(to_katakana(s.reading or s.text)):
                        if base_idx >= len(base):
                            raise OutputError("end of base reached before end of reading")

                        if c != base[base_idx]:
                            if i < len(unit.segments) - 1:
                                use_special_base = True
                            elif s.reading:
                                raise OutputError("last segment has a reading")

                            if not use_special_base:
                                common_pref = s.text[:k]
                                if common_pref:
                                    yield common_pref
                                yield f"[{s.text[k:]}={unit.base_form[base_idx:]}]"
                                return
                        base_idx += 1

                if s.reading:
                    yield f"[{s.text}|{s.reading}]"
                else:
                    yield s.text
            if use_special_base:
                return True
            elif add_accent and base and base_idx < len(base):
                yield f"[={unit.base_form[base_idx:]}]"

        special_base = False
        itr = segment_strs(unit, _add_accent(unit))
        str_list = []
        try:
            while True:
                str_list.append(next(itr))
        except StopIteration as si:
            if si.value:
                special_base = True
        segment_str = "".join(str_list)
        if _add_accent(unit):
            sp_base = "|" + unit.base_form if special_base else ""
            return f"{{{segment_str};{','.join(accent_strs(unit))}{sp_base}}}"
        else:
            return segment_str

    return "".join(map(fmt_unit, units))
