from normalize import comp_kana, has_kana, is_kana, to_hiragana


class Segment:
    text: str
    reading: str | None

    def __init__(self, text: str, reading: str | None = None):
        self.text = text
        if reading and not comp_kana(text, reading):
            self.reading = reading
        else:
            self.reading = None

    def __repr__(self):
        return f"S[{self.text},{self.reading}]"

    @classmethod
    def generate(cls, word: str, reading: str | None) -> list["Segment"]:
        def segmentalize(reading: str, sections: list[str],
                         rs_idx: int, re_idx: int, s_idx: int,
                         segments: list[cls]) -> list[cls] | None:
            if s_idx >= len(sections):
                if rs_idx < len(reading):
                    return None
                else:
                    return segments

            sect = sections[s_idx]
            if not is_kana(sect):
                new_seg = segments + [Segment(sect, reading[rs_idx:re_idx])]
            else:
                if reading[rs_idx:re_idx] == sect:
                    new_seg = segments + [Segment(sect)]
                else:
                    return None
            if re_idx == len(reading):
                return new_seg
            for nre in range(re_idx + 1, len(reading) + 1):
                res = segmentalize(reading, sections, re_idx, nre, s_idx + 1, new_seg)
                if res:
                    return res
            return None

        if not reading:
            return [Segment(word)]

        if comp_kana(reading, word):
            return [cls(word)]

        reading = to_hiragana(reading)
        if not has_kana(word):
            return [cls(word, reading)]

        sections = []
        last_start = 0
        kana = is_kana(word[0])
        for i, c in enumerate(word):
            kana_at_i = is_kana(c)
            if kana_at_i != kana:
                sections.append(word[last_start:i])
                last_start = i
                kana = kana_at_i
        sections.append(word[last_start:])

        res = None
        for re in range(1, len(reading) + 1):
            res = segmentalize(reading, sections, 0, re, 0, [])
            if res:
                break
        return res if res else [Segment(word, reading)]


class Unit:
    segments: list[Segment]
    accents: list[int]
    base_form: str | None
    uncertain: bool

    def __init__(self, segments: list[Segment],
                 accents: list[int] | None = None,
                 base_form: str | None = None,
                 uncertain: bool = False):
        self.segments = segments
        self.accents = accents or []
        self.base_form = base_form
        self.uncertain = uncertain

    def __repr__(self):
        return f"U[{self.segments},{self.accents},{self.base_form}{';uncertain' if self.uncertain else ''}]"

    def reading(self, upper: int | None = None):
        return "".join(map(lambda s: s.reading or s.text, self.segments[:upper]))

    def text(self, upper: int | None = None):
        return "".join(map(lambda s: s.text, self.segments[:upper]))
