from html.parser import HTMLParser
from typing import List, MutableSequence, Optional, Sequence, Tuple

from .segments import replace_nbsp

_void_tags = {"area", "base", "br", "col", "command", "embed", "hr", "img", "input", "keygen", "link", "meta", "param",
              "source", "track", "wbr"}
_block_tags = {"blockquote", "dd", "div", "dl", "dt", "figcaption", "figure", "hr", "li", "ol", "p", "pre", "ul"}
_break_tags = {"br", "hr"}

_follow_omit_map = {
    "dd": {"dd", "dt"},
    "dt": {"dd", "dt"},
    "li": {"li"},
    "optgroup": {"optgroup"},
    "option": {"option", "optgroup"},
    "p": {"address", "article", "aside", "blockquote", "details", "div", "dl", "fieldset", "figcaption", "figure",
          "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hgroup", "hr", "main", "menu", "nav", "ol",
          "p", "pre", "section", "table", "ul"},
    "rp": {"rp", "rt"},
    "rt": {"rp", "rt"},
    "tbody": {"tbody", "tfoot"},
    "td": {"td", "th"},
    "th": {"td", "th"},
    "thead": {"tbody", "tfoot"},
    "tr": {"tr"},
}

_end_omit = {"dd", "li", "optgroup", "option", "p", "rp", "rt", "tbody", "td", "tfoot", "th", "tr"}
_p_no_end_omit = {"a", "audio", "del", "ins", "map", "noscript", "video"}


class JrpHTMLParser(HTMLParser):
    tag_stack: List[str]
    lines: List[str]
    cur_line: List[str]

    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.lines = []
        self.cur_line = []

    def _insert_line(self, is_break: bool = False):
        line: str = "".join(self.cur_line).strip()
        if line or is_break:
            self.lines.append(line)
        self.cur_line = []

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        def handle_omission(tag_stack: MutableSequence[str], start_tag: str) -> Optional[str]:
            if not tag_stack:
                return None
            stack_tag: str = tag_stack[-1]
            if stack_tag in _follow_omit_map and start_tag in _follow_omit_map[stack_tag]:
                return tag_stack.pop()

        omitted_tag = handle_omission(self.tag_stack, tag)
        if omitted_tag and omitted_tag in _block_tags or tag in _block_tags or tag in _break_tags:
            self._insert_line(is_break=tag == "br")
        if tag not in _void_tags:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        def handle_omission(tag_stack: MutableSequence[str], end_tag: str) -> Optional[str]:
            if not tag_stack:
                return None
            stack_tag: str = tag_stack[-1]
            if end_tag != stack_tag and stack_tag in _end_omit:
                if stack_tag != "p" or (end_tag not in _p_no_end_omit):
                    return tag_stack.pop()
            return None

        omitted_tag = handle_omission(self.tag_stack, tag)
        if tag in _block_tags or omitted_tag and omitted_tag in _block_tags:
            self._insert_line()
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

    def handle_data(self, data: str) -> None:
        self.cur_line.append(data)

    def close(self) -> List[str]:
        super().close()
        self._insert_line()
        return self.lines


def strip_html(val: str, norm_nbsp: bool = True) -> List[str]:
    parser = JrpHTMLParser()
    parser.feed(val)
    return [replace_nbsp(line) if norm_nbsp else line for line in parser.close()]
