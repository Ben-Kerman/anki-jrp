import os
from dataclasses import dataclass, field
from enum import Enum, auto
from subprocess import PIPE, Popen
from typing import List, Optional, Tuple

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
    SETUBI = auto()
    SYMBOL = auto()
    NUMBER = auto()
    OTHER = auto()


@dataclass
class MecabUnit(ParserUnit):
    hinsi: str
    hinsi_class_1: Optional[str] = None
    hinsi_class_2: Optional[str] = None
    hinsi_class_3: Optional[str] = None
    conj_type: Optional[str] = None
    conj_form: Optional[str] = None
    base_form: Optional[str] = None
    reading: Optional[str] = None
    pronunciation: Optional[str] = None

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
        if self.hinsi == "助詞" or self.hinsi == "助動詞":
            return HinsiType.ZYOSI
        elif self.hinsi == "動詞" or self.hinsi == "形容詞":
            return HinsiType.YOUGEN
        elif self.hinsi == "記号":
            return HinsiType.SYMBOL
        elif self.hinsi == "名詞":
            if self.hinsi_class_1 == "接尾":
                return HinsiType.SETUBI
            elif self.hinsi_class_1 == "数":
                return HinsiType.NUMBER
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

    def base_reading(self) -> Optional[str]:
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
    def from_line(cls, line: str) -> Tuple["MecabUnit", int, int]:
        def raise_on_ast(val: str) -> str:
            if val == "*":
                raise MecabError("unexpected empty value in unit")
            else:
                return val

        def ast_to_none(val: str) -> Optional[str]:
            return None if val == "*" else val

        # format: %m(表層形)\t%ps,%pe,%H(品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音)
        orig: str
        data: str
        try:
            orig, data = line.split("\t", 1)
        except ValueError:
            raise MecabError(f"invalid line: {line}")

        fields = data.split(",")
        if len(fields) < 3 or (fields[2] != "未知語" and len(fields) != 11):
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
    exe_path: Optional[str] = None
    dic_dir: Optional[str] = None
    _inst: Optional[Popen] = field(default=None, init=False)

    def _instance(self) -> Popen:
        if self._inst is None or self._inst.poll() is not None:
            args = [self.exe_path] if self.exe_path else ["mecab"]
            args.extend(("--unk-feature=未知語", "--node-format=%m\\t%ps,%pe,%H\\n"))
            if self.exe_path:
                args.append(f"--rcfile={os.path.join(os.path.dirname(self.exe_path), 'mecabrc')}")
            if self.dic_dir:
                args.append(f"--dicdir={self.dic_dir}")

            try:
                self._inst = Popen(args, stdin=PIPE, stdout=PIPE)
            except FileNotFoundError:
                raise MecabError("executable not found")

        return self._inst

    def analyze(self, txt: str) -> List[ParserUnit]:
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
