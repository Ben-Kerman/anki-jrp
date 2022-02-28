from dataclasses import dataclass, field
from enum import Enum, auto

from .normalize import comp_kana, has_kana, is_kana, split_moras, to_hiragana, to_katakana
from .util import escape_text as esc


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

    def fmt(self, escape: bool = False) -> str:
        txt, rdng = self.text, self.reading
        if escape:
            txt, rdng = esc('|=]', txt) if rdng else esc("{[;}", txt), esc(']', rdng) if rdng else rdng
        return f"[{txt}|{rdng}]" if rdng else txt

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

        result = None
        for re in range(1, len(reading) + 1):
            result = segmentalize(reading, sections, 0, re, 0, [])
            if result:
                break
        return result if result else [Segment(word, reading)]


@dataclass
class BaseSegment:
    text: str | None
    base: str

    def __repr__(self) -> str:
        return f"BS[{self.text}={self.base}]"

    def fmt(self, escape: bool = False) -> str:
        txt, base = self.text or "", self.base
        if escape:
            txt, base = (esc('|=]', txt) if txt else ""), esc(']', base)
        return f"[{txt}={base}]"


@dataclass
class Unit:
    segments: list[Segment | BaseSegment]
    accents: list[int] = field(default_factory=list)
    is_yougen: bool = False
    uncertain: bool = False
    special_base: str | None = None
    was_bare: bool = False

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

    def base_reading(self) -> str | None:
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
                  accents: list[int] | None = None, is_yougen: bool = False, uncertain: bool = False,
                  was_bare: bool = False) -> "Unit":
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

        return cls(segments, accents or [], is_yougen, uncertain, special_base, was_bare)


class ParsingError(ValueError):
    pass


def _read_until(val: str, idx: int, stop: tuple[str, ...]) -> tuple[int, str | None, str]:
    chars: list[str] = []
    itr = enumerate(val[idx:])
    for i, c in itr:
        if c in stop:
            return idx + i, c, "".join(chars)
        elif c == "\\":
            match next(itr, None):
                case [_, esc_c]:
                    chars.append(esc_c)
                case None:
                    raise ParsingError("backslash at end of input")
        else:
            chars.append(c)
    return len(val), None, "".join(chars)


def _parse_migaku_accents(val: str, reading: str, has_base: bool) -> list[int]:
    def convert(tag: str, moras: int, has_base: bool) -> int:
        match tag[0]:
            case "h":
                return 0
            case "a":
                if has_base:
                    print("atamadaka in non-yougen accent list")
                return 1
            case "k":
                if not has_base:
                    print("kifuku in non-yougen accent list")
                return int(tag[1:])
            case "n":
                if has_base:
                    print("nakadaka in yougen accent list")
                return int(tag[1:])
            case "o":
                if has_base:
                    print("odaka in yougen accent list")
                return moras
            case _:
                raise ParsingError(f"invalid Migaku accent pattern: {tag}")

    moras = len(split_moras(reading))
    tags = val.split(",")
    return [convert(t, moras, has_base) for t in tags]


def parse_migaku(value: str, conv_en_spaces: bool = True) -> list[Unit]:
    class State(Enum):
        BASE_READING = auto()
        ACCENTS = auto()
        SUFFIX = auto()

    @dataclass
    class Parser:
        val: str
        pos: int

        def __init__(self, val: str):
            self.val = val
            self.pos = 0

        def skip_space(self):
            while self.pos < len(self.val) and self.val[self.pos] == " ":
                self.pos += 1

        def read_text(self, stop: tuple[str, ...]) -> tuple[str | None, str]:
            full_stop = stop + ("<",)
            parts = []
            while True:
                stop_pos, stop_c, txt = _read_until(self.val, self.pos, full_stop)
                parts.append(txt)
                if not stop_c or stop_c in stop:
                    self.pos = stop_pos + 1
                    return stop_c, "".join(parts)
                else:
                    tag_end_pos, tag_end_c, tag_cont = _read_until(self.val, stop_pos, (">",))
                    if not tag_end_c:
                        raise ParsingError(f"Unclosed HTML tag: {tag_cont}")
                    else:
                        self.pos = tag_end_pos + 1
                        parts.append(tag_cont)
                        parts.append(">")

        def parse_unit(self) -> Unit:
            state: State
            prefix: str
            prefix_reading: str

            prfx_end_c, prefix = self.read_text(("[", " "))
            if conv_en_spaces:
                prefix = prefix.replace(chr(0x2002), " ")
            if prfx_end_c == " " or not prfx_end_c:
                return Unit([Segment(prefix)], was_bare=True)

            rdng_end_c, prefix_reading = self.read_text((",", ";", "]"))
            match rdng_end_c:
                case ",":
                    state = State.BASE_READING
                case ";":
                    state = State.ACCENTS
                case "]":
                    state = State.SUFFIX
                case _:
                    raise ParsingError(f"unclosed Migaku tag: {self.val}")

            base_reading: str = ""
            if state == State.BASE_READING:
                bsfm_end_c, base_reading = self.read_text((";", "]"))
                match bsfm_end_c:
                    case ";":
                        state = State.ACCENTS
                    case "]":
                        state = State.SUFFIX
                    case _:
                        raise ParsingError(f"unclosed Migaku tag: {self.val}")

            accent_str: str = ""
            if state == State.ACCENTS:
                acct_end, acct_c, accent_str = _read_until(self.val, self.pos, ("]",))
                match acct_c:
                    case "]":
                        state = State.SUFFIX
                    case _:
                        raise ParsingError(f"closing ] missing: {self.val}")
                self.pos = acct_end + 1

            suffix: str = ""
            if state == State.SUFFIX:
                _, suffix = self.read_text((" ",))

            text = prefix + suffix
            reading = prefix_reading + suffix if prefix_reading else None
            accents = _parse_migaku_accents(accent_str, reading or text, bool(base_reading)) if accent_str else None
            return Unit.from_text(text, reading, base_reading or None, accents, bool(base_reading))

        def execute(self) -> list[Unit]:
            units = []
            while self.pos < len(self.val):
                self.skip_space()
                units.append(self.parse_unit())
            return units

    return Parser(value).execute()


def parse_jrp(value: str) -> list[Unit]:
    def parse_segment(val: str, start_idx: int) -> tuple[int, Segment | BaseSegment]:
        sep_idx, sep_c, seg_text = _read_until(val, start_idx + 1, ("|", "="))
        if sep_c:
            cls = BaseSegment if sep_c == "=" else Segment
            end_idx, end_c, reading = _read_until(val, sep_idx + 1, ("]",))
            if not end_c:
                raise ParsingError(f"segment is missing closing bracket: {val}")
            return end_idx + 1, cls(seg_text, reading)
        raise ParsingError(f"invalid segment: {val}")

    def parse_unit(val: str, start_idx: int) -> tuple[int, Unit]:
        segments: list[Segment | BaseSegment] = []

        pos = start_idx + 1
        while pos < len(val):
            pos, last_c, txt = _read_until(val, pos, ("[", ";", "}"))
            if txt:
                segments.append(Segment(txt))

            match last_c:
                case "[":
                    pos, s = parse_segment(val, pos)
                    segments.append(s)
                case ";" | "}":
                    break
        else:
            raise ParsingError(f"unclosed unit: {val}")

        accents: list[int] = []
        special_base: str | None = None
        uncertain = False
        is_yougen = False
        if val[pos] == ";":
            pos += 1
            if val[pos] == "!":
                uncertain = True
                pos += 1
            if val[pos] == "Y":
                is_yougen = True
                pos += 1

            end_idx, end_c, accent_str = _read_until(val, pos, ("|", "}"))
            if end_c:
                try:
                    accents = [int(acc) for acc in accent_str.split(",")]
                except ValueError:
                    raise ParsingError(f"invalid accent: {val}")
            else:
                raise ParsingError(f"unclosed unit: {val}")

            if end_c == "|":
                unit_end_idx, ec, special_base = _read_until(val, end_idx + 1, ("}",))
                if ec:
                    pos = unit_end_idx
                else:
                    raise ParsingError(f"unclosed unit: {val}")
            else:
                pos = end_idx

        return pos + 1, Unit(segments, accents, is_yougen, uncertain, special_base)

    units: list[Unit] = []
    free_segments: list[Segment] = []

    idx = 0
    while idx < len(value):
        idx, c, text = _read_until(value, idx, ("[", "{"))
        if text:
            free_segments.append(Segment(text))

        match c:
            case "{":
                if free_segments:
                    units.append(Unit(free_segments, was_bare=True))
                free_segments = []
                idx, u = parse_unit(value, idx)
                units.append(u)
            case "[":
                idx, segment = parse_segment(value, idx)
                if type(segment) != Segment:  # TODO maybe allow
                    raise ParsingError(f"base form segment outside of unit: {value}")
                free_segments.append(segment)

    if free_segments:
        units.append(Unit(free_segments, was_bare=True))

    return units
