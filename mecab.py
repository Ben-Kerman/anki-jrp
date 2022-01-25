import re
from subprocess import PIPE, Popen

_unit_re = re.compile(r"(?P<orig>.+)\t"
                      r"(?P<hinsi>.+),"
                      r"(?P<hinsi_class_1>.+),"
                      r"(?P<hinsi_class_2>.+),"
                      r"(?P<hinsi_class_3>.+),"
                      r"(?P<conj_type>.+),"
                      r"(?P<conj_form>.+),"
                      r"(?P<base_form>.+),"
                      r"(?P<reading>.+),"
                      r"(?P<pronunciation>.+)")


class MecabException(Exception):
    pass


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
        m = _unit_re.fullmatch(res)
        if m is None:
            raise MecabException
        else:
            self.orig: str = m.group("orig")
            self.hinsi: str = m.group("hinsi")
            self.hinsi_class_1: str = m.group("hinsi_class_1")
            self.hinsi_class_2: str = m.group("hinsi_class_2")
            self.hinsi_class_3: str = m.group("hinsi_class_3")
            self.conj_type: str = m.group("conj_type")
            self.conj_form: str = m.group("conj_form")
            self.base_form: str = m.group("base_form")
            self.reading: str = m.group("reading")
            self.pronunciation: str = m.group("pronunciation")

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
        self._inst = Popen(["mecab"], stdin=PIPE, stdout=PIPE)

    def _instance(self) -> Popen:
        if self._inst is None:
            self._init()
        return self._inst

    def analyze(self, txt: str) -> [str]:
        inst = self._instance()
        inst.stdin.write(txt.encode("utf-8") + b"\n")
        inst.stdin.flush()
        while (line := inst.stdout.readline().rstrip(b"\r\n")) != b"EOS":
            print(MecabUnit(line.decode("utf-8")))
