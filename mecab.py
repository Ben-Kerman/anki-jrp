import re
from subprocess import PIPE, Popen

from util import warn

_unit_re = re.compile(r"(?P<hinsi>.+?),"
                      r"(?P<hinsi_class_1>.+?),"
                      r"(?P<hinsi_class_2>.+?),"
                      r"(?P<hinsi_class_3>.+?),"
                      r"(?P<conj_type>.+?),"
                      r"(?P<conj_form>.+?),"
                      r"(?P<base_form>.+?),"
                      r"(?P<reading>.+?),"
                      r"(?P<pronunciation>.+?)")


class MecabException(Exception):
    pass


def raise_ast(val: str) -> str:
    if val == "*":
        raise MecabException("unexpected empty value in unit")
    else:
        return val


def handle_ast(val: str) -> str | None:
    return None if val == "*" else val


class MecabUnit:
    orig: str | None
    hinsi: str | None
    hinsi_class_1: str | None
    hinsi_class_2: str | None
    hinsi_class_3: str | None
    conj_type: str | None
    conj_form: str | None
    base_form: str | None
    reading: str | None
    pronunciation: str | None

    def __init__(self, res: str):
        orig, data = res.split("\t", 1)
        self.orig = raise_ast(orig)
        if data == "未知語":
            self.hinsi = "未知語"
            self.hinsi_class_1 = None
            self.hinsi_class_2 = None
            self.hinsi_class_3 = None
            self.conj_type = None
            self.conj_form = None
            self.base_form = None
            self.reading = None
            self.pronunciation = None
        else:
            m = _unit_re.fullmatch(data)
            if m is None:
                warn(f"invalid MeCab unit: {res}")
                raise MecabException("invalid unit")
            else:
                self.hinsi = raise_ast(m.group("hinsi"))
                self.hinsi_class_1 = handle_ast(m.group("hinsi_class_1"))
                self.hinsi_class_2 = handle_ast(m.group("hinsi_class_2"))
                self.hinsi_class_3 = handle_ast(m.group("hinsi_class_3"))
                self.conj_type = handle_ast(m.group("conj_type"))
                self.conj_form = handle_ast(m.group("conj_form"))
                self.base_form = raise_ast(m.group("base_form"))
                self.reading = raise_ast(m.group("reading"))
                self.pronunciation = raise_ast(m.group("pronunciation"))

    def __repr__(self):
        return "MecabUnit[" \
               f"{self.orig}:" \
               f"{self.hinsi}," \
               f"{self.hinsi_class_1}," \
               f"{self.hinsi_class_2}," \
               f"{self.hinsi_class_3}," \
               f"{self.conj_type}," \
               f"{self.conj_form}," \
               f"{self.base_form}," \
               f"{self.reading}," \
               f"{self.pronunciation}]"


class Mecab:
    _inst: Popen | None

    def __init__(self):
        self._inst = None

    def _init(self):
        self._inst = Popen(["mecab", "--unk-feature=未知語"], stdin=PIPE, stdout=PIPE)

    def _instance(self) -> Popen:
        if self._inst is None or self._inst.poll() is not None:
            try:
                self._init()
            except FileNotFoundError:
                raise MecabException("executable not found")
        return self._inst

    def analyze(self, txt: str) -> [str]:
        inst = self._instance()
        inst.stdin.write(txt.encode("utf-8") + b"\n")
        inst.stdin.flush()
        units = []
        while (line := inst.stdout.readline().rstrip(b"\r\n")) != b"EOS":
            units.append(MecabUnit(line.decode("utf-8")))
        return units
