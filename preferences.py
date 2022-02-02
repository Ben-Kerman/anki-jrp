class ConvPrefs:
    prefer_accent_lookups: bool
    yougen_join_nai: bool
    yougen_join_u: bool
    yougen_join_ta: bool
    yougen_join_te: bool
    yougen_join_ba: bool
    yougen_join_sou: bool
    dousi_join_zu: bool
    dousi_join_reru: bool
    dousi_join_seru: bool
    dousi_join_masu: bool
    dousi_join_tyau: bool
    dousi_split_teru: bool

    def __init__(self,
                 prefer_accent_lookups: bool = False,
                 yougen_join_nai: bool = True,
                 yougen_join_u: bool = True,
                 yougen_join_ta: bool = True,
                 yougen_join_te: bool = True,
                 yougen_join_ba: bool = True,
                 yougen_join_sou: bool = True,
                 dousi_join_zu: bool = True,
                 dousi_join_reru: bool = True,
                 dousi_join_seru: bool = True,
                 dousi_join_masu: bool = True,
                 dousi_join_tyau: bool = False,
                 dousi_split_teru: bool = True):
        self.prefer_accent_lookups = prefer_accent_lookups
        self.yougen_join_nai = yougen_join_nai
        self.yougen_join_u = yougen_join_u
        self.yougen_join_ta = yougen_join_ta
        self.yougen_join_te = yougen_join_te
        self.yougen_join_ba = yougen_join_ba
        self.yougen_join_sou = yougen_join_sou
        self.dousi_join_zu = dousi_join_zu
        self.dousi_join_reru = dousi_join_reru
        self.dousi_join_seru = dousi_join_seru
        self.dousi_join_masu = dousi_join_masu
        self.dousi_join_tyau = dousi_join_tyau
        self.dousi_split_teru = dousi_split_teru


class Prefs:
    conv: ConvPrefs
