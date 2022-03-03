from enum import Enum, auto


class WidgetType(Enum):
    Checkbox = auto()
    Number = auto()
    Color = auto()
    Directory = auto()
    File = auto()
    Text = auto()


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

output_defs = [
    "Output preferences",
    {
        "name": "min_accent_moras",
        "desc": "Minimum accent moras",
        "tool": "Never add accent information to hiragana-only words "
                "with less than this amount of moras.",
        "type": WidgetType.Number
    }, {
        "name": "katakana_min_accent",
        "desc": "Ignore minimum accent katakana",
        "tool": "Ignore any kana-only words below the minimum mora count, not just hiragana.",
        "type": WidgetType.Checkbox
    }
]

_path_tt = "Relative paths are resolved with the addon's install directory as the base."

addon_defs = [
    "Add-on preferences",
    {
        "name": "mecab_path",
        "desc": "MeCab executable path",
        "tool": _path_tt,
        "type": WidgetType.File
    }, {
        "name": "mecab_dict_dir",
        "desc": "MeCab dictionary directory",
        "tool": _path_tt,
        "type": WidgetType.Directory
    }, {
        "name": "mecab_use_system_exe",
        "desc": "Use system-wide MeCab executable",
        "type": WidgetType.Checkbox
    }, {
        "name": "mecab_use_system_dict",
        "desc": "Use MeCab system dictionary",
        "type": WidgetType.Checkbox
    }
]

_shared_tt = "\nUpdates will happen when saving any relevant change to the preferences " \
             "and when opening Anki for the first time after an add-on update."

nt_checkboxes = [
    {
        "path": ("manage_script",),
        "desc": "Manage script",
        "tool": "Automatically insert and update the script "
                "that converts pitch accent syntax to HTML elements "
                "into all card templates of this note type." + _shared_tt
    },
    {
        "path": ("manage_style",),
        "desc": "Manage stylesheet",
        "tool": "Automatically insert and update the configured stylesheet "
                "into this note type." + _shared_tt
    }
]

style_defs = [
    "Values will be inserted into CSS as-is, without any verification",
    {
        "name": "use_diamond_indicators",
        "desc": "Use diamond indicators",
        "tool": "Use Migaku-style diamonds as accent indicators instead of bars.",
        "type": WidgetType.Checkbox
    }, {
        "name": "highlight_split_accents",
        "desc": "Highlight split accents",
        "tool": "Highlight split accents (e.g. ゼ↓ンダイ・ミ→モン) "
                "by adding a text shadow in the second accent pattern's color.\n"
                "If disabled, words with split accent will appear as though their accent is unknown. "
                "The indicator will still work properly, "
                "except for the first accent of a word when using diamonds.",
        "type": WidgetType.Checkbox
    }, {
        "name": "ruby_font_size",
        "desc": "Ruby (furigana) font size",
        "tool": "--jrp-ruby-font-size",
        "type": WidgetType.Text
    }, {
        "name": "graph_font_size",
        "desc": "Accent graph font size",
        "tool": "--jrp-graph-font-size",
        "type": WidgetType.Text
    }, {
        "name": "heiban",
        "desc": "Heiban color",
        "tool": "--jrp-heiban",
        "type": WidgetType.Color
    }, {
        "name": "kifuku",
        "desc": "Kifuku color",
        "tool": "--jrp-kifuku",
        "type": WidgetType.Color
    }, {
        "name": "atamadaka",
        "desc": "Atamadaka color",
        "tool": "--jrp-atamadaka",
        "type": WidgetType.Color
    }, {
        "name": "odaka",
        "desc": "Odaka color",
        "tool": "--jrp-odaka",
        "type": WidgetType.Color
    }, {
        "name": "nakadaka",
        "desc": "Nakadaka color",
        "tool": "--jrp-nakadaka",
        "type": WidgetType.Color
    }, {
        "name": "unknown",
        "desc": "Unknown accent color",
        "tool": "--jrp-unknown",
        "type": WidgetType.Color
    }, {
        "name": "uncertain_opacity",
        "desc": "Opacity of words with uncertain accent",
        "tool": "--jrp-uncertain-opacity",
        "type": WidgetType.Text
    }, {
        "name": "graph_border_width",
        "desc": "Accent graph border width",
        "tool": "--jrp-graph-border-width",
        "type": WidgetType.Text
    }, {
        "name": "graph_border_radius",
        "desc": "Accent graph border radius",
        "tool": "--jrp-graph-border-radius",
        "type": WidgetType.Text
    }, {
        "name": "graph_bg_light",
        "desc": "Graph background color (light mode)",
        "tool": "--jrp-graph-bg-light",
        "type": WidgetType.Color
    }, {
        "name": "graph_border_light",
        "desc": "Graph border color (light mode)",
        "tool": "--jrp-graph-border-light",
        "type": WidgetType.Color
    }, {
        "name": "graph_bg_dark",
        "desc": "Graph background color (dark mode)",
        "tool": "--jrp-graph-bg-dark",
        "type": WidgetType.Color
    }, {
        "name": "graph_border_dark",
        "desc": "Graph border color (dark mode)",
        "tool": "--jrp-graph-border-dark",
        "type": WidgetType.Color
    }, {
        "name": "indicator_bar_width",
        "desc": "Accent indicator bar width",
        "tool": "--jrp-indicator-bar-width",
        "type": WidgetType.Text
    }, {
        "name": "indicator_bar_radius",
        "desc": "Accent indicator bar border radius",
        "tool": "--jrp-indicator-bar-radius",
        "type": WidgetType.Text
    }, {
        "name": "indicator_bar_gap",
        "desc": "Gap between accent indicator bars",
        "tool": "--jrp-indicator-bar-gap",
        "type": WidgetType.Text
    }, {
        "name": "indicator_bar_margin",
        "desc": "Margin at the side of indicator bars",
        "tool": "--jrp-indicator-bar-margin",
        "type": WidgetType.Text
    }, {
        "name": "indicator_bar_offset",
        "desc": "Offset of bars in horizontal text (横書き)",
        "tool": "--jrp-indicator-bar-offset",
        "type": WidgetType.Text
    }, {
        "name": "indicator_bar_offset_vert",
        "desc": "Offset of bars in vertical text (縦書き)",
        "tool": "--jrp-indicator-bar-offset-vert",
        "type": WidgetType.Text
    }, {
        "name": "indicator_diamond_size",
        "desc": "Size of accent indicator diamonds",
        "tool": "--jrp-indicator-diamond-size",
        "type": WidgetType.Text
    }
]
