from dataclasses import dataclass


@dataclass
class Accent:
    value: int | list[tuple[int, int]]

    @classmethod
    def from_str(cls, val: str) -> "Accent":
        return Accent(int(val))  # TODO support compounds

    from_json = from_str

    def __str__(self) -> str:
        if type(self.value) is int:
            return str(self.value)
        else:
            return "-".join(f"{acc}@{moras}" for acc, moras in self.value)

    def migaku_str(self) -> str:
        pass  # TODO
