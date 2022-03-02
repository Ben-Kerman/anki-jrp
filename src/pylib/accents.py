from dataclasses import dataclass

from .normalize import split_moras


@dataclass
class Accent:
    value: int | list[tuple[int, int]] | None

    @classmethod
    def from_str(cls, val: str, mora_count: int | None = None) -> "Accent":
        def parse_part(v: str) -> tuple[int, int | None]:
            split = v.split("@")
            if len(split) == 1:
                return int(v), None
            elif len(split) == 2:
                return int(split[0]), int(split[1])
            else:
                raise ValueError

        if val == "?":
            return Accent(None)

        part_strs = val.split("-")
        if len(part_strs) > 1:
            parts = [parse_part(p) for p in part_strs]
            if any(not mc for _, mc in parts[:-1]):
                raise ValueError

            [ds_mora, raw_mc] = parts[-1]
            if raw_mc is None:
                if mora_count is None:
                    raise ValueError
                else:
                    calc_count = mora_count - sum(mc for _, mc in parts[:-1])
                    parts[-1] = (ds_mora, calc_count)

            return Accent(parts)
        else:
            return Accent(int(val))

    from_json = from_str

    def __str__(self) -> str:
        if self.value is None:
            return "?"
        elif type(self.value) is int:
            return str(self.value)
        else:
            return "-".join(f"{acc}@{moras}" for acc, moras in self.value)

    def __repr__(self) -> str:
        return f"A[{self}]"

    def __hash__(self) -> int:
        if type(self.value) is not list:
            return hash(self.value)
        else:
            return hash(tuple(self.value))

    def fmt_migaku(self, reading: str, is_yougen: bool) -> str:
        if self.value is None:
            return "?"

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
