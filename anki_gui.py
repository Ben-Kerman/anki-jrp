import re
from collections.abc import Callable, Sequence
from typing import Any, Iterable, TypeVar

import aqt.utils
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QCheckBox, QColorDialog, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLayout, \
    QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from aqt.notetypechooser import NotetypeChooser

import anki_ui_defs
import overrides
import util
from anki_ui_defs import StyleTypes
from overrides import AccentOverride, DefaultOverride, IgnoreOverride, WordOverride
from preferences import NoteTypePrefs, Prefs


def _get(obj, path: Iterable[str]):
    val = obj
    for name in path:
        val = getattr(val, name)
    return val


def _set(obj, path: Sequence[str], new_val):
    val = obj
    for name in path[:-1]:
        val = getattr(val, name)
    setattr(val, path[-1], new_val)


class Checkbox(QWidget):
    prefs: Prefs
    defaults: Prefs
    path: Sequence[str]

    _cb: QCheckBox
    _btn: QPushButton
    _lo: QHBoxLayout

    def __init__(self, label: str, prefs: Prefs, defaults: Prefs, path: Sequence[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.prefs = prefs
        self.defaults = defaults
        self.path = path

        self._btn = QPushButton(QIcon(util.get_path("assets", "reset.svg")), "", self)
        self._btn.setFlat(True)
        sp = self._btn.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self._btn.setSizePolicy(sp)
        self._btn.setToolTip("Reset to default")
        self._btn.clicked.connect(self.reset)

        self._cb = QCheckBox(label, self)
        self._cb.stateChanged.connect(self.state_change)
        self._cb.setChecked(_get(prefs, path))
        self.state_change(self._cb.isChecked())

        self._lo = QHBoxLayout(self)
        self._lo.setContentsMargins(0, 0, 0, 0)
        self._lo.addWidget(self._cb, 1)
        self._lo.addWidget(self._btn)

    def state_change(self, new_state: int):
        new_state = bool(new_state)
        _set(self.prefs, self.path, new_state)
        if new_state != _get(self.defaults, self.path):
            self._btn.show()
        else:
            self._btn.hide()

    def reset(self):
        def_val = _get(self.defaults, self.path)
        self._cb.setChecked(def_val)


def _insert_cbs(defs: list[str | dict], wdgt: QWidget, lo: QLayout, prefs: Any, defaults: Any):
    for item in defs:
        if type(item) == str:
            lo.addWidget(QLabel(item, wdgt))
        else:
            cb = Checkbox(item["desc"], prefs, defaults, item["path"], wdgt)
            if "tool" in item:
                cb.setToolTip(item["tool"])
            lo.addWidget(cb)


class DefaultOverrideCheckbox(QCheckBox):
    id_set: set[int]
    override: DefaultOverride

    def __init__(self, id_set: set[int], override: DefaultOverride, parent: QWidget | None = None):
        super().__init__(override.value.fmt(), parent)
        self.id_set = id_set
        self.override = override

        self.setChecked(override.id not in id_set)
        self.stateChanged.connect(self.state_change)

    def state_change(self, state: int):
        if state:
            self.id_set.discard(self.override.id)
        else:
            self.id_set.add(self.override.id)


T = TypeVar("T")


def _split(txt: str, sep: str = "・", conv: Callable[[str], T] = lambda s: s) -> list[T]:
    return [conv(v) for v in (v.strip() for v in txt.split(sep)) if v]


def _new(self, new_or) -> None:
    self._ors.append(new_or)
    rc = self._tbl.rowCount()
    self._tbl.setRowCount(rc + 1)
    self.insert_row(rc, new_or)


def _del(self) -> None:
    cr = self._tbl.currentRow()
    if cr < 0:
        aqt.utils.showWarning("No row selected")
        return
    del self._ors[cr]
    self._tbl.removeRow(cr)


def _setup_btns(self, default: Callable) -> QHBoxLayout:
    btn_bar = QHBoxLayout()
    new_btn = QPushButton("New", self)
    new_btn.clicked.connect(lambda: _new(self, default()))
    btn_bar.addWidget(new_btn)
    del_btn = QPushButton("Delete", self)
    del_btn.clicked.connect(lambda: _del(self))
    btn_bar.addWidget(del_btn)
    return btn_bar


class IgnoreOverrideWidget(QWidget):
    _ors: list[IgnoreOverride]
    _tbl: QTableWidget

    def __init__(self, ors: list[IgnoreOverride], parent: QWidget | None = None):
        super().__init__(parent)
        self._ors = ors

        self._tbl = QTableWidget(len(ors), 2, self)
        self._tbl.setHorizontalHeaderLabels(("Variants", "Reading"))
        for row, ior in enumerate(ors):
            self.insert_row(row, ior)
        self._tbl.cellChanged.connect(self.on_change)
        self._tbl.itemActivated.connect(lambda i: self._tbl.editItem(i))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ignored Words", self))
        layout.addLayout(_setup_btns(self, lambda: IgnoreOverride(["漢字"], "よみ")))
        layout.addWidget(self._tbl, 1)

    def insert_row(self, r: int, ovrd: IgnoreOverride):
        self._tbl.setItem(r, 0, QTableWidgetItem("・".join(ovrd.variants)))
        self._tbl.setItem(r, 1, QTableWidgetItem(ovrd.reading))

    def on_change(self, row: int, col: int):
        item = self._tbl.item(row, col)
        override = self._ors[row]
        txt = item.text().strip()

        if col == 0:
            if not txt:
                aqt.utils.showWarning("At least one variant is required")
                item.setText("・".join(override.variants))
            else:
                override.variants = _split(txt)
        else:
            override.reading = txt or None

        print(self._ors)


class WordOverrideWidget(QWidget):
    _ors: list[WordOverride]
    _tbl: QTableWidget

    def __init__(self, ors: list[WordOverride], parent: QWidget | None = None):
        super().__init__(parent)
        self._ors = ors

        self._tbl = QTableWidget(len(ors), 6, self)
        self._tbl.setHorizontalHeaderLabels(("Old Variants", "Old Reading",
                                             "New Variants", "New Reading",
                                             "Pre", "Post"))
        for row, wor in enumerate(ors):
            self.insert_row(row, wor)
        self._tbl.cellChanged.connect(self.on_change)
        self._tbl.itemActivated.connect(lambda i: self._tbl.editItem(i))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Word Overrides", self))
        layout.addLayout(_setup_btns(self, lambda: WordOverride(["旧"], new_variants=["新"])))
        layout.addWidget(self._tbl, 1)

    def insert_row(self, r: int, ovrd: WordOverride):
        def make_cb(attr_name: str) -> QCheckBox:
            cb = QCheckBox(self)
            cb.setChecked(getattr(ovrd, attr_name))
            cb.stateChanged.connect(lambda s: setattr(ovrd, attr_name, bool(s)))
            return cb

        self._tbl.setItem(r, 0, QTableWidgetItem("・".join(ovrd.old_variants)))
        self._tbl.setItem(r, 1, QTableWidgetItem(ovrd.old_reading or ""))
        self._tbl.setItem(r, 2, QTableWidgetItem("・".join(ovrd.new_variants or [])))
        self._tbl.setItem(r, 3, QTableWidgetItem(ovrd.new_reading or ""))
        self._tbl.setCellWidget(r, 4, make_cb("pre_lookup"))
        self._tbl.setCellWidget(r, 5, make_cb("post_lookup"))

    def on_change(self, row: int, col: int):
        item = self._tbl.item(row, col)
        override = self._ors[row]
        txt = item.text().strip()

        if col == 0:
            if not txt:
                aqt.utils.showWarning("At least one variant is required")
                item.setText("・".join(override.old_variants))
            else:
                override.old_variants = _split(txt)
        elif col == 1:
            override.old_reading = txt or None
        elif col == 2:
            if not txt and not override.new_reading:
                aqt.utils.showWarning("New variants and reading can't both be empty")
                item.setText("・".join(override.new_variants or []))
            else:
                override.new_variants = _split(txt) if txt else None
        else:
            if not txt and not override.new_variants:
                aqt.utils.showWarning("New variants and reading can't both be empty")
                item.setText(override.new_reading)
            else:
                override.new_reading = txt or None


class AccentOverrideWidget(QWidget):
    _ors: list[AccentOverride]
    _tbl: QTableWidget

    def __init__(self, ors: list[AccentOverride], parent: QWidget | None = None):
        super().__init__(parent)
        self._ors = ors

        self._tbl = QTableWidget(len(ors), 3, self)
        self._tbl.setHorizontalHeaderLabels(("Variants", "Reading", "Accents"))
        for row, aor in enumerate(ors):
            self.insert_row(row, aor)
        self._tbl.cellChanged.connect(self.on_change)
        self._tbl.itemActivated.connect(lambda i: self._tbl.editItem(i))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Accent Overrides", self))
        layout.addLayout(_setup_btns(self, lambda: AccentOverride(["漢字"], "よみ", [0])))
        layout.addWidget(self._tbl, 1)

    def insert_row(self, r: int, ovrd: AccentOverride):
        self._tbl.setItem(r, 0, QTableWidgetItem("・".join(ovrd.variants)))
        self._tbl.setItem(r, 1, QTableWidgetItem(ovrd.reading))
        self._tbl.setItem(r, 2, QTableWidgetItem(", ".join(map(str, ovrd.accents))))

    def on_change(self, row: int, col: int):
        item = self._tbl.item(row, col)
        override = self._ors[row]
        txt = item.text().strip()

        if col == 0:
            if not txt:
                aqt.utils.showWarning("At least one variant is required")
                item.setText("・".join(override.variants))
            else:
                override.variants = _split(txt)
        elif col == 1:
            if not txt:
                aqt.utils.showWarning("Reading is required")
                item.setText(override.reading)
            else:
                override.reading = txt
        else:
            if not txt:
                aqt.utils.showWarning("At least one accent is required")
                item.setText(", ".join(map(str, override.accents)))
            else:
                override.accents = _split(txt, ",", int)


class ColorWidget(QWidget):
    _le: QLineEdit
    _picker: QColorDialog

    value_changed = pyqtSignal(str)

    def __init__(self, init_val: str):
        super().__init__()

        self._picker = QColorDialog(self)
        self._picker.colorSelected.connect(lambda qc: self.set_value(qc.name().lower()))

        lo = QHBoxLayout(self)
        self._le = QLineEdit()
        self._le.textEdited.connect(lambda txt: self.set_value(txt, True))
        lo.addWidget(self._le, 1)
        col_btn = QPushButton("Pick")
        col_btn.clicked.connect(lambda: self._picker.show())
        lo.addWidget(col_btn)

        lo.setContentsMargins(0, 0, 0, 0)

        self.set_value(init_val)

    def set_value(self, val: str, from_text: bool = False):
        if not from_text:
            self._le.setText(val)
        if m := re.match(r"#([\da-f]{2})([\da-f]{2})([\da-f]{2})", val.strip(), re.I):
            qcolor = QColor(int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
        else:
            qcolor = QColor(0xff, 0xff, 0xff)
        self._picker.setCurrentColor(qcolor)
        self.value_changed.emit(val.strip())


class NoteTypeWidget(QFrame):
    def __init__(self, nt_prefs: NoteTypePrefs, parent: QWidget | None = None):
        super().__init__(parent)
        defaults = NoteTypePrefs(0)

        style_dialog = QDialog(self)
        style_dialog.setWindowTitle("Note Type Style")
        style_dialog.setWindowModality(Qt.ApplicationModal)
        style_lo = QFormLayout(style_dialog)
        style_lo.addRow(QLabel("Values will be inserted into CSS as-is, without any verification"))
        style_prefs = nt_prefs.style
        for item in anki_ui_defs.style_widgets:
            val = getattr(style_prefs, item["name"])
            lbl = QLabel(f"{item['desc']}:")
            tt = f"CSS variable: {item['vnme']}"
            lbl.setToolTip(tt)
            if item["type"] == StyleTypes.Any:
                edit_wdgt = QLineEdit(val)
                edit_wdgt.textEdited.connect(lambda txt: setattr(style_prefs, item["name"], txt.strip()))
            elif item["type"] == StyleTypes.Color:
                edit_wdgt = ColorWidget(val)
                edit_wdgt.value_changed.connect(lambda c: setattr(style_prefs, item["name"], c))
            else:
                raise Exception("invalid enum variant in UI definition")
            edit_wdgt.setToolTip(tt)
            style_lo.addRow(lbl, edit_wdgt)

        top_lo = QHBoxLayout()
        top_lo.addWidget(QLabel(aqt.mw.col.models.get(nt_prefs.nt_id)["name"]), 1)
        style_btn = QPushButton("Edit Style", self)
        style_btn.clicked.connect(lambda: style_dialog.show())
        top_lo.addWidget(style_btn)

        bottom_lo = QHBoxLayout()
        _insert_cbs(anki_ui_defs.nt_checkboxes, self, bottom_lo, nt_prefs, defaults)

        base_lo = QVBoxLayout(self)
        base_lo.addLayout(top_lo)
        base_lo.addLayout(bottom_lo)

        self.setFrameShape(QFrame.Box)


class NoteTypesWidget(QWidget):
    _ntc: NotetypeChooser
    _lst: list[NoteTypePrefs]
    _lo: QVBoxLayout

    def __init__(self, nt_pref_list: list[NoteTypePrefs], parent: QWidget | None = None):
        super().__init__(parent)
        self._lst = nt_pref_list

        self._ntc = NotetypeChooser(mw=aqt.mw, widget=QWidget(),
                                    starting_notetype_id=aqt.mw.col.models.all_names_and_ids()[0].id)
        add_btn = QPushButton("Add", self)
        add_btn.clicked.connect(self.add_new)
        add_lo = QHBoxLayout()
        add_lo.addWidget(self._ntc)
        add_lo.addWidget(add_btn)

        self._lo = QVBoxLayout(self)
        self._lo.addLayout(add_lo)
        for nt_prefs in nt_pref_list:
            self._lo.addWidget(NoteTypeWidget(nt_prefs, self))
        self._lo.addStretch()

    def add_new(self):
        nt_id = self._ntc.selected_notetype_id
        if any(nt_id == p.nt_id for p in self._lst):
            aqt.utils.showWarning("This note type has already been added.")
        else:
            prefs = NoteTypePrefs(nt_id)
            self._lst.append(prefs)
            self._lo.insertWidget(self._lo.count() - 1, NoteTypeWidget(prefs, self))


class PreferencesWidget(QTabWidget):
    def __init__(self, prefs: Prefs, parent: QWidget | None = None):
        super().__init__(parent)
        defaults = Prefs()

        conv_wdgt = QWidget(self)

        conv_lo = QVBoxLayout()
        _insert_cbs(anki_ui_defs.conv_checkboxes, conv_wdgt, conv_lo, prefs, defaults)
        conv_lo.addStretch()

        default_ors = overrides.defaults()
        dor_lo = QVBoxLayout()
        dor_lo.addWidget(QLabel("Words ignored by default:", conv_wdgt))
        for dior in default_ors.ignore:
            dor_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.ignore, dior, conv_wdgt))
        dor_lo.addWidget(QLabel("Default word overrides:", conv_wdgt))
        for dwor in default_ors.word:
            dor_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.word, dwor, conv_wdgt))
        dor_lo.addWidget(QLabel("Default accent overrides:", conv_wdgt))
        for daor in default_ors.accent:
            dor_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.accent, daor, conv_wdgt))
        dor_lo.addStretch()

        conv_dor_lo = QHBoxLayout(conv_wdgt)
        conv_dor_lo.addLayout(conv_lo)
        conv_dor_lo.addLayout(dor_lo, 1)

        override_wdgt = QWidget(self)
        override_lo = QHBoxLayout(override_wdgt)
        override_lo.addWidget(IgnoreOverrideWidget(prefs.convert.overrides.ignore, override_wdgt))
        override_lo.addWidget(WordOverrideWidget(prefs.convert.overrides.word, override_wdgt))
        override_lo.addWidget(AccentOverrideWidget(prefs.convert.overrides.accent, override_wdgt))

        self.addTab(conv_wdgt, "Conversion")
        self.addTab(override_wdgt, "Overrides")
