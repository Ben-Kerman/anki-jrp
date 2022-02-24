from enum import Enum, auto

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


class StyleTypes(Enum):
    Color = auto()
    Any = auto()


style_widgets = [
    {
        "name": "ruby_font_size",
        "vnme": "--jrp-ruby-font-size",
        "desc": "Ruby (furigana) font size",
        "type": StyleTypes.Any
    }, {
        "name": "graph_font_size",
        "vnme": "--jrp-graph-font-size",
        "desc": "Accent graph font size",
        "type": StyleTypes.Any
    }, {
        "name": "heiban",
        "vnme": "--jrp-heiban",
        "desc": "Heiban color",
        "type": StyleTypes.Color
    }, {
        "name": "kifuku",
        "vnme": "--jrp-kifuku",
        "desc": "Kifuku color",
        "type": StyleTypes.Color
    }, {
        "name": "atamadaka",
        "vnme": "--jrp-atamadaka",
        "desc": "Atamadaka color",
        "type": StyleTypes.Color
    }, {
        "name": "odaka",
        "vnme": "--jrp-odaka",
        "desc": "Odaka color",
        "type": StyleTypes.Color
    }, {
        "name": "nakadaka",
        "vnme": "--jrp-nakadaka",
        "desc": "Nakadaka color",
        "type": StyleTypes.Color
    }, {
        "name": "graph_border_width",
        "vnme": "--jrp-graph-border-width",
        "desc": "Accent graph border width",
        "type": StyleTypes.Any
    }, {
        "name": "graph_border_radius",
        "vnme": "--jrp-graph-border-radius",
        "desc": "Accent graph border radius",
        "type": StyleTypes.Any
    }, {
        "name": "graph_bg_light",
        "vnme": "--jrp-graph-bg-light",
        "desc": "Graph background color (light mode)",
        "type": StyleTypes.Color
    }, {
        "name": "graph_border_light",
        "vnme": "--jrp-graph-border-light",
        "desc": "Graph border color (light mode)",
        "type": StyleTypes.Color
    }, {
        "name": "graph_bg_dark",
        "vnme": "--jrp-graph-bg-dark",
        "desc": "Graph background color (dark mode)",
        "type": StyleTypes.Color
    }, {
        "name": "graph_border_dark",
        "vnme": "--jrp-graph-border-dark",
        "desc": "Graph border color (dark mode)",
        "type": StyleTypes.Color
    }, {
        "name": "indicator_bar_width",
        "vnme": "--jrp-indicator-bar-width",
        "desc": "Accent indicator bar width",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_bar_radius",
        "vnme": "--jrp-indicator-bar-radius",
        "desc": "Accent indicator bar border radius",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_bar_gap",
        "vnme": "--jrp-indicator-bar-gap",
        "desc": "Gap between accent indicator bars",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_bar_margin",
        "vnme": "--jrp-indicator-bar-margin",
        "desc": "Margin at the side of indicator bars",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_bar_offset",
        "vnme": "--jrp-indicator-bar-offset",
        "desc": "Offset of bars in horizontal text (横書き)",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_bar_offset_vert",
        "vnme": "--jrp-indicator-bar-offset-vert",
        "desc": "Offset of bars in vertical text (縦書き)",
        "type": StyleTypes.Any
    }, {
        "name": "indicator_diamond_size",
        "vnme": "--jrp-indicator-diamond-size",
        "desc": "Size of accent indicator diamonds",
        "type": StyleTypes.Any
    }
]
