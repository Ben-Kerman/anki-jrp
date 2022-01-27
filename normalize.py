_hira = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ"
_kata = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ"
_to_hira_tbl = str.maketrans(_kata, _hira)
_to_kata_tbl = str.maketrans(_hira, _kata)


def to_hiragana(val: str) -> str:
    return val.translate(_to_hira_tbl)


def to_katakana(val: str) -> str:
    return val.translate(_to_kata_tbl)
