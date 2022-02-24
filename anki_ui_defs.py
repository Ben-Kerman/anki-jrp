conv_checkboxes = [
    "General conversion settings",
    {
        "path": ("convert", "prefer_accent_lookups"),
        "desc": "Prefer adding accents over readings"
    },
    "Join preferences for 動詞・形容詞",
    {
        "path": ("convert", "join", "yougen_join_nai"),
        "desc": "Join ない（知らない・早くない）"
    }, {
        "path": ("convert", "join", "yougen_join_u"),
        "desc": "Join う（知ろう・早かろう）"
    }, {
        "path": ("convert", "join", "yougen_join_ta"),
        "desc": "Join た（知った・早かった）"
    }, {
        "path": ("convert", "join", "yougen_join_te"),
        "desc": "Join て（知って・早くて）"
    }, {
        "path": ("convert", "join", "yougen_join_ba"),
        "desc": "Join ば（知れば・早ければ）"
    }, {
        "path": ("convert", "join", "yougen_join_sou"),
        "desc": "Join そう（知りそう・早そう）"
    }, {
        "path": ("convert", "join", "keiyousi_join_sa"),
        "desc": "Join さ（早さ）"
    }, {
        "path": ("convert", "join", "dousi_join_tai"),
        "desc": "Join たい（知りたい）"
    }, {
        "path": ("convert", "join", "dousi_join_nu"),
        "desc": "Join ぬ（知らぬ）"
    }, {
        "path": ("convert", "join", "dousi_join_n"),
        "desc": "Join ん（知らん）"
    }, {
        "path": ("convert", "join", "dousi_join_reru"),
        "desc": "Join れる（知られる）"
    }, {
        "path": ("convert", "join", "dousi_join_seru"),
        "desc": "Join せる（知らせる）"
    }, {
        "path": ("convert", "join", "dousi_join_masu"),
        "desc": "Join ます（知ります）"
    }, {
        "path": ("convert", "join", "dousi_join_tyau"),
        "desc": "Join ちゃう（知っちゃう）"
    }, {
        "path": ("convert", "join", "dousi_split_teru"),
        "desc": "Split てる（知って・る）"
    }
]

nt_checkboxes = [
    {
        "path": ("manage_script",),
        "desc": "Manage script",
        "tool": "Automatically insert and update the script "
                "that converts pitch accent syntax into HTML elements "
                "into all card templates of this note type"
    },
    {
        "path": ("manage_style",),
        "desc": "Manage stylesheet",
        "tool": "Automatically insert and update the configured stylesheet "
                "into this note type."
    },
    {
        "path": ("use_diamond_indicators",),
        "desc": "Use diamond accent indicators"
    },
    {
        "path": ("remove_mia_migaku",),
        "desc": "Remove code managed by MIA/Migaku",
        "tool": "Attempt to remove any scripts and stylesheets "
                "from the Migaku (formerly MIA) Japanese addon "
                "when managed code is inserted or updated"
    }
]
