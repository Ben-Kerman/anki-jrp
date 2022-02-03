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
                         r_idx: int, s_idx: int,
                         segments: list[cls]) -> list[cls] | None:
            if s_idx >= len(sections):
                if r_idx < len(reading):
                    return None
                else:
                    return segments

            sect = sections[s_idx]
            if not is_kana(sect):
                return segmentalize(reading, sections, r_idx, s_idx + 1, segments)

            m_idx = r_idx
            while m_idx < len(reading):
                m_idx = reading.find(to_hiragana(sect), m_idx)
                if m_idx >= 0:
                    n_segm = [Segment(sections[s_idx - 1], reading[r_idx:m_idx])] if s_idx > 0 else []
                    n_segm.append(Segment(sect))
                    if s_idx == len(sections) - 2:
                        return n_segm + [Segment(sections[-1], reading[m_idx + len(sect):])]
                    else:
                        nxt = segmentalize(reading, sections, m_idx + len(sect), s_idx + 2, segments + n_segm)
                        if nxt:
                            return nxt
                    m_idx += 1
                else:
                    break
            return None

        if not reading:
            return [Segment(word)]

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

        res = segmentalize(reading, sections, 0, 0, [])
        return res if res else [Segment(word, reading)]


class Unit:
    segments: list[Segment]
    accents: list[int]
    base_form: str | None

    def __init__(self, segments: list[Segment],
                 accents: list[int] | None = None,
                 base_form: str | None = None):
        self.segments = segments
        self.accents = accents or []
        self.base_form = base_form

    def __repr__(self):
        return f"U[{self.segments},{self.accents},{self.base_form}]"

    def reading(self, upper: int | None = None):
        return "".join(map(lambda s: s.reading or s.text, self.segments[:upper]))

    def text(self, upper: int | None = None):
        return "".join(map(lambda s: s.text, self.segments[:upper]))
