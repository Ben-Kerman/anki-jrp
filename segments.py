from dataclasses import dataclass, field
from enum import Enum, auto

from normalize import comp_kana, has_kana, is_kana, to_hiragana, to_katakana
from util import empty_list, split_moras, warn


@dataclass
class Segment:
    text: str
    reading: str | None

    def __init__(self, text: str, reading: str | None = None):
        self.text = text
        if reading and not comp_kana(text, reading):
            self.reading = reading
        else:
            self.reading = None

    def __repr__(self) -> str:
        return f"S[{self.text}|{self.reading}]"

    def fmt(self) -> str:
        return f"[{self.text}|{self.reading}]" if self.reading else self.text

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
            if s_idx == len(sections) - 1 and re_idx == len(reading):
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


@dataclass
class BaseSegment:
    text: str | None
    base: str

    def __repr__(self) -> str:
        return f"BS[{self.text}={self.base}]"

    def fmt(self) -> str:
        return f"[{self.text or ''}={self.base}]"


@dataclass
class Unit:
    segments: list[Segment | BaseSegment]
    accents: list[int] = field(default_factory=empty_list)
    is_yougen: bool = False
    uncertain: bool = False
    special_base: str | None = None

    def __repr__(self) -> str:
        yougen = ",用言" if self.is_yougen else ""
        uncert = ",不確" if self.uncertain else ""
        specbs = f"|{self.special_base}" if self.special_base else ""
        return f"U[{self.segments},{self.accents}{yougen}{uncert}{specbs}]"

    def non_base_segments(self) -> list[Segment]:
        segments: list[Segment] = []
        for s in self.segments:
            match s:
                case Segment():
                    segments.append(s)
                case BaseSegment():
                    if s.text:
                        if segments and not segments[-1].reading:
                            segments[-1] = Segment(segments[-1].text + s.text)
                        else:
                            segments.append(Segment(s.text))
                case _:
                    raise ValueError(f"invalid segment type")
        return segments

    def reading(self, upper: int | None = None) -> str:
        return "".join(map(lambda s: s.reading or s.text, self.non_base_segments()[:upper]))

    def text(self, upper: int | None = None) -> str:
        return "".join(map(lambda s: s.text, self.non_base_segments()[:upper]))

    def base_form(self) -> str | None:
        if self.special_base:
            return self.special_base
        elif any(type(s) == BaseSegment for s in self.segments):
            def process_segment(s: Segment | BaseSegment) -> str:
                match s:
                    case Segment():
                        return s.reading or s.text
                    case BaseSegment():
                        return s.base
                    case _:
                        raise ValueError("invalid segment type")

            return "".join([process_segment(s) for s in self.segments])
        elif self.is_yougen:
            return self.reading()
        else:
            return None

    @classmethod
    def from_text(cls, text: str, reading: str | None = None, base: str | None = None,
                  accents: list[int] | None = None, is_yougen: bool = False, uncertain: bool = False) -> "Unit":
        def base_segments(segments: list[Segment], base: str) -> list[Segment | BaseSegment] | str | None:
            new_segments = []

            k_base = to_katakana(base)
            base_idx = 0
            for i, s in enumerate(segments):
                for k, c in enumerate(to_katakana(s.reading or s.text)):
                    if base_idx > len(k_base):
                        return base

                    if c != k_base[base_idx]:
                        if i < len(segments) - 1 or s.reading:
                            return base

                        if k > 0:
                            new_segments.append(Segment(s.text[:k]))
                        new_segments.append(BaseSegment(s.text[k:], base[base_idx:]))
                        return new_segments
                    base_idx += 1
                new_segments.append(s)
            if base_idx < len(base):
                new_segments.append(BaseSegment(None, base[base_idx:]))
                return new_segments
            return None

        segments = Segment.generate(text, reading)
        special_base = None
        if is_yougen:
            match base_segments(segments, base):
                case list(new_segments):
                    segments = new_segments
                case str(special):
                    special_base = special

        return cls(segments, accents or [], is_yougen, uncertain, special_base)


class ParsingError(ValueError):
    pass


def _multi_find(val: str, idx: int, stop: tuple[str, ...]) -> tuple[int, str | None]:
    for i in range(idx, len(val)):
        if val[i] in stop:
            return i, val[i]
    return len(val), None


def _parse_migaku_accents(val: str, reading: str, has_base: bool) -> list[int]:
    def convert(tag: str, moras: int, has_base: bool) -> int:
        match tag[0]:
            case "h":
                return 0
            case "a":
                if has_base:
                    warn("atamadaka in non-yougen accent list")
                return 1
            case "k":
                if not has_base:
                    warn("kifuku in non-yougen accent list")
                return int(tag[1:])
            case "n":
                if has_base:
                    warn("nakadaka in yougen accent list")
                return int(tag[1:])
            case "o":
                if has_base:
                    warn("odaka in yougen accent list")
                return moras
            case _:
                raise ParsingError(f"invalid Migaku accent pattern: {tag}")

    moras = len(split_moras(reading))
    tags = val.split(",")
    return [convert(t, moras, has_base) for t in tags]


def parse_migaku(val: str) -> list[Unit]:
    class State(Enum):
        PREFIX = auto()
        READING = auto()
        BASE_FORM = auto()
        ACCENTS = auto()
        SUFFIX = auto()

    @dataclass
    class Parser:
        val: str
        pos: int

        def advance(self, new_pos: int) -> str:
            rv = self.val[self.pos:new_pos]
            self.pos = new_pos + 1
            return rv

        def parse_unit(self) -> Unit:
            state: State = State.PREFIX

            prefix: str = ""
            prefix_reading: str = ""
            base_form: str = ""
            accent_str: str = ""
            suffix: str = ""

            prfx_end, prfx_c = _multi_find(self.val, self.pos, ("[", " "))
            match prfx_c:
                case " " | None:
                    segments = [Segment(self.val[self.pos:prfx_end])]
                    self.pos = prfx_end + 1
                    return Unit(segments)
                case "[":
                    prefix = self.advance(prfx_end)

            rdng_end, rdng_c = _multi_find(self.val, self.pos, (",", ";", "]"))
            match rdng_c:
                case ",":
                    state = State.BASE_FORM
                case ";":
                    state = State.ACCENTS
                case "]":
                    state = State.SUFFIX
                case _:
                    raise ParsingError(f"unclosed Migaku tag: {self.val}")
            prefix_reading = self.advance(rdng_end)

            if state == State.BASE_FORM:
                bsfm_end, bsfm_c = _multi_find(self.val, self.pos, (";", "]"))
                match bsfm_c:
                    case ";":
                        state = State.ACCENTS
                    case "]":
                        state = State.SUFFIX
                    case _:
                        raise ParsingError(f"unclosed Migaku tag: {self.val}")
                base_form = self.advance(bsfm_end)

            if state == State.ACCENTS:
                acct_end, acct_c = _multi_find(self.val, self.pos, ("]",))
                match acct_c:
                    case "]":
                        state = State.SUFFIX
                    case _:
                        raise ParsingError(f"closing ] missing: {self.val}")
                accent_str = self.advance(acct_end)

            if state == State.SUFFIX:
                sufx_end, _ = _multi_find(self.val, self.pos, (" ",))
                suffix = self.advance(sufx_end)

            text = prefix + suffix
            reading = prefix_reading + suffix if prefix_reading else None
            accents = _parse_migaku_accents(accent_str, reading or text, bool(base_form)) if accent_str else None
            return Unit.from_text(text, reading, base_form or None, accents, bool(base_form))

        def execute(self) -> list[Unit]:
            units = []
            while self.pos < len(self.val):
                units.append(self.parse_unit())
            return units

    return Parser(val, 0).execute()


def parse_jrp(val: str) -> list[Unit]:
    def parse_segment(val: str, idx: int) -> tuple[int, Segment | BaseSegment]:
        def parse_reading(val: str, idx: int) -> tuple[int, str]:
            pos, _ = _multi_find(val, idx, ("]",))
            if pos >= 0:
                return pos, val[idx:pos]

        sep_idx, sep_c = _multi_find(val, idx, ("|", "="))
        if sep_c:
            cls = BaseSegment if sep_c == "=" else Segment
            end_idx, reading = parse_reading(val, sep_idx + 1)
            return end_idx + 1, cls(val[idx:sep_idx], reading)
        raise ParsingError(f"invalid segment: {val}")

    def parse_unit(val: str, idx: int) -> tuple[int, Unit]:
        segments: list[Segment | BaseSegment] = []
        cur_text = []

        def insert_segment():
            nonlocal segments, cur_text
            if cur_text:
                segments.append(Segment("".join(cur_text)))
            cur_text = []

        ended = False
        has_accents = False
        while idx < len(val):
            match val[idx]:
                case "[":
                    insert_segment()
                    idx, s = parse_segment(val, idx + 1)
                    segments.append(s)
                case ";":
                    insert_segment()
                    idx += 1
                    has_accents = True
                    break
                case "}":
                    ended = True
                    break
                case c:
                    cur_text.append(c)
                    idx += 1

        if not has_accents and not ended:
            raise ParsingError(f"unclosed unit: {val}")

        accents = None
        special_base = None
        uncertain = False
        is_yougen = False
        if has_accents:
            end_idx, c = _multi_find(val, idx, ("|", "}"))
            if c:
                if val[idx] == "!":
                    uncertain = True
                    idx += 1
                if val[idx] == "Y":
                    is_yougen = True
                    idx += 1

                try:
                    accents = [int(acc) for acc in val[idx:end_idx].split(",")]
                except ValueError:
                    raise ParsingError(f"invalid accent: {val}")
            if c == "|":
                unit_end_idx, ec = _multi_find(val, end_idx + 1, ("}",))
                if ec:
                    special_base = val[end_idx + 1:unit_end_idx]
                    idx = unit_end_idx
                else:
                    raise ParsingError(f"unclosed unit: {val}")
            else:
                idx = end_idx

        return idx + 1, Unit(segments, accents, is_yougen, uncertain, special_base)

    units: list[Unit] = []
    segments: list[Segment] = []
    cur_text = []

    def insert_segment():
        nonlocal segments, cur_text
        if cur_text:
            segments.append(Segment("".join(cur_text)))
        cur_text = []

    idx = 0
    while idx < len(val):
        match val[idx]:
            case "{":
                insert_segment()
                if segments:
                    units.append(Unit(segments))
                segments = []
                idx, u = parse_unit(val, idx + 1)
                units.append(u)
            case "[":
                insert_segment()
                idx, s = parse_segment(val, idx + 1)
                if type(s) != Segment:
                    raise ParsingError(f"base form segment outside of unit: {val}")
                segments.append(s)
            case c:
                cur_text.append(c)
                idx += 1

    if cur_text:
        insert_segment()
    if segments:
        units.append(Unit(segments))

    return units
