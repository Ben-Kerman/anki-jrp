from dataclasses import dataclass, field
from enum import Enum, auto
from subprocess import PIPE, Popen

from .normalize import is_kana, to_hiragana


class MecabError(Exception):
    pass


@dataclass
class ParserUnit:
    value: str

    def __repr__(self):
        return f"InputUnit[{self.value}]"


class HinsiType(Enum):
    ZYOSI = auto()
    YOUGEN = auto()
    SYMBOL = auto()
    OTHER = auto()


@dataclass
class MecabUnit(ParserUnit):
    hinsi: str
    hinsi_class_1: str | None = None
    hinsi_class_2: str | None = None
    hinsi_class_3: str | None = None
    conj_type: str | None = None
    conj_form: str | None = None
    base_form: str | None = None
    reading: str | None = None
    pronunciation: str | None = None

    def __repr__(self):
        return "MecabUnit[" \
               f"{self.value}:" \
               f"{self.hinsi}," \
               f"{self.hinsi_class_1}," \
               f"{self.hinsi_class_2}," \
               f"{self.hinsi_class_3}," \
               f"{self.conj_type}," \
               f"{self.conj_form}," \
               f"{self.base_form}," \
               f"{self.reading}," \
               f"{self.pronunciation}]"

    def hinsi_type(self) -> HinsiType:
        match self.hinsi:
            case "助詞" | "助動詞":
                return HinsiType.ZYOSI
            case "動詞" | "形容詞":
                return HinsiType.YOUGEN
            case "記号":
                return HinsiType.SYMBOL
            case _:
                return HinsiType.OTHER

    def comp_hinsi(self, *args: str):
        if self.hinsi != args[0]:
            return False
        if len(args) > 1 and self.hinsi_class_1 != args[1]:
            return False
        if len(args) > 2 and self.hinsi_class_2 != args[2]:
            return False
        if len(args) > 3 and self.hinsi_class_3 != args[3]:
            return False
        return True

    def base_reading(self) -> str | None:
        if self.hinsi_type() != HinsiType.YOUGEN:
            return None

        if is_kana(self.base_form):
            return self.base_form

        itr = enumerate(zip(reversed(self.value), reversed(self.reading)))
        for i, (co, cr) in itr:
            if co != cr:
                break
        else:
            return None

        return self.reading[0:len(self.reading) - i] + self.base_form[len(self.value) - i:]

    @classmethod
    def from_line(cls, line: str) -> tuple["MecabUnit", int, int]:
        def raise_on_ast(val: str) -> str:
            if val == "*":
                raise MecabError("unexpected empty value in unit")
            else:
                return val

        def ast_to_none(val: str) -> str | None:
            return None if val == "*" else val

        # format: %m(表層形)\t%ps,%pe,%H(品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音)
        orig: str
        data: str
        try:
            orig, data = line.split("\t", 1)
        except ValueError:
            raise MecabError(f"invalid line: {line}")

        fields = data.split(",")
        if len(fields) != 11:
            raise MecabError(f"invalid number of fields: {line}")

        if fields[2] != "未知語":
            obj = cls(orig, fields[2],
                      ast_to_none(fields[3]),
                      ast_to_none(fields[4]),
                      ast_to_none(fields[5]),
                      ast_to_none(fields[6]),
                      ast_to_none(fields[7]),
                      raise_on_ast(fields[8]),
                      to_hiragana(raise_on_ast(fields[9])),
                      to_hiragana(raise_on_ast(fields[10])))
        else:
            obj = cls(orig, fields[2])
        return obj, int(fields[0]), int(fields[1])


@dataclass
class Mecab:
    exe_path: str | None = None
    dic_dir: str | None = None
    _inst: Popen | None = field(default=None, init=False)

    def _init(self):
        args = [self.exe_path] if self.exe_path else ["mecab"]
        args.extend(("--unk-feature=未知語", "--node-format=%m\\t%ps,%pe,%H\\n"))
        if self.dic_dir:
            args.append(f"--dicdir={self.dic_dir}")
        self._inst = Popen(args, stdin=PIPE, stdout=PIPE)

    def _instance(self) -> Popen:
        if self._inst is None or self._inst.poll() is not None:
            try:
                self._init()
            except FileNotFoundError:
                raise MecabError("executable not found")
        return self._inst

    def analyze(self, txt: str) -> list[ParserUnit]:
        inst = self._instance()
        utf8_bytes = txt.encode("utf-8")
        inst.stdin.write(utf8_bytes + b"\n")
        inst.stdin.flush()
        units = []
        last_end = 0
        while (line := inst.stdout.readline().rstrip(b"\r\n")) != b"EOS":
            unit, start, end = MecabUnit.from_line(line.decode("utf-8"))
            if last_end != start:
                units.append(ParserUnit(utf8_bytes[last_end:start].decode("utf-8")))
            last_end = end
            units.append(unit)
        return units
