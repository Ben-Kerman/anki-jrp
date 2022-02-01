from dataclasses import dataclass
from subprocess import PIPE, Popen


class MecabException(Exception):
    pass


@dataclass
class ParserUnit:
    value: str

    def __repr__(self):
        return f"InputUnit[{self.value}]"


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

    @classmethod
    def from_line(cls, line: str) -> tuple["MecabUnit", int, int]:
        def raise_on_ast(val: str) -> str:
            if val == "*":
                raise MecabException("unexpected empty value in unit")
            else:
                return val

        def ast_to_none(val: str) -> str | None:
            return None if val == "*" else val

        # format: %m(表層形)\t%ps,%pe,%H(品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音)
        orig: str
        data: str
        orig, data = line.split("\t", 1)
        fields = data.split(",")
        if fields[2] != "未知語":
            obj = cls(orig, fields[2],
                      ast_to_none(fields[3]),
                      ast_to_none(fields[4]),
                      ast_to_none(fields[5]),
                      ast_to_none(fields[6]),
                      ast_to_none(fields[7]),
                      raise_on_ast(fields[8]),
                      raise_on_ast(fields[9]),
                      raise_on_ast(fields[10]))
        else:
            obj = cls(orig, fields[2])
        return obj, int(fields[0]), int(fields[1])


class Mecab:
    _inst: Popen | None

    def __init__(self):
        self._inst = None

    def _init(self):
        self._inst = Popen(["mecab", "--unk-feature=未知語", "--node-format=%m\\t%ps,%pe,%H\\n"], stdin=PIPE, stdout=PIPE)

    def _instance(self) -> Popen:
        if self._inst is None or self._inst.poll() is not None:
            try:
                self._init()
            except FileNotFoundError:
                raise MecabException("executable not found")
        return self._inst

    def analyze(self, txt: str) -> list[MecabUnit]:
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
