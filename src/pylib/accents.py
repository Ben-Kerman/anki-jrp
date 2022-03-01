from dataclasses import dataclass

from src.pylib.normalize import split_moras


@dataclass
class Accent:
    value: int | list[tuple[int, int | None]]

    @classmethod
    def from_str(cls, val: str) -> "Accent":
        return Accent(int(val))  # TODO support compounds

    from_json = from_str

    def __str__(self) -> str:
        if type(self.value) is int:
            return str(self.value)
        else:
            return "-".join(f"{acc}@{moras}" for acc, moras in self.value)

    def fmt_migaku(self, reading: str, is_yougen: bool) -> str:
        moras = split_moras(reading)

        def fmt_part(downstep: int, mora_count: int) -> str:
            if downstep == 0:
                return "h"
            elif is_yougen:
                return f"k{downstep}"
            elif downstep == 1:
                return "a"
            elif downstep == mora_count:
                return "o"
            else:
                return f"n{downstep}"

        if type(self.value) is int:
            return fmt_part(self.value, len(moras))
        else:
            if self.value[-1][1] is None:
                last_mc = len(moras) - sum(mc for _, mc in self.value[:-1])
            else:
                last_mc = self.value[-1][1]
            parts = [fmt_part(ds, mc) for ds, mc in self.value[:-1]] + [fmt_part(self.value[-1][0], last_mc)]
            return "".join(parts)
