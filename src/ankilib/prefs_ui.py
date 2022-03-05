from collections.abc import Callable
from copy import deepcopy
from enum import Enum, auto
from typing import TypeVar

import aqt.utils
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, \
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from aqt.notetypechooser import NotetypeChooser

from . import global_vars, prefs_ui_defs as ui_defs
from .common_ui import add_form_row, insert_checkboxes
from .templates import remove_mia_migaku, update_script, update_style
from ..pylib import overrides
from ..pylib.accents import Accent
from ..pylib.overrides import AccentOverride, DefaultOverride, IgnoreOverride, WordOverride
from ..pylib.preferences import NoteTypePrefs, Prefs, StylePrefs

_DEFAULT_PREFS = Prefs()
_DEFAULT_NT_PREFS = NoteTypePrefs(0)


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
        hh = self._tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)

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
        hh = self._tbl.horizontalHeader()
        for i in range(4):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)

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
        elif not txt and not override.new_variants:
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
        hh = self._tbl.horizontalHeader()
        for i in range(3):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)

        for row, aor in enumerate(ors):
            self.insert_row(row, aor)
        self._tbl.cellChanged.connect(self.on_change)
        self._tbl.itemActivated.connect(lambda i: self._tbl.editItem(i))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Accent Overrides", self))
        layout.addLayout(_setup_btns(self, lambda: AccentOverride(["漢字"], "よみ", [Accent(0)])))
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
            def reset_acc():
                item.setText(", ".join(map(str, override.accents)))

            if not txt:
                aqt.utils.showWarning("At least one accent is required")
                reset_acc()
            else:
                try:
                    override.accents = _split(txt, ",", Accent.from_str)
                except ValueError:
                    aqt.utils.showWarning("Invalid accent syntax")
                    reset_acc()


class NoteTypesWidget(QWidget):
    _ntc: NotetypeChooser
    _lst: list[NoteTypePrefs]
    _lo: QVBoxLayout

    def __init__(self, nt_pref_list: list[NoteTypePrefs], parent: QWidget | None = None):
        super().__init__(parent)
        self._lst = nt_pref_list

        ntc_wdgt = QWidget(self)
        self._ntc = NotetypeChooser(mw=aqt.mw, widget=ntc_wdgt,
                                    starting_notetype_id=aqt.mw.col.models.all_names_and_ids()[0].id)
        add_btn = QPushButton("Add", self)
        add_btn.clicked.connect(self.add_new)
        add_lo = QHBoxLayout()
        add_lo.addWidget(ntc_wdgt)
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

    def remove(self, wdgt: "NoteTypeWidget", prefs: NoteTypePrefs):
        nt_dict = aqt.mw.col.models.get(prefs.nt_id)
        nt_name = f"'{nt_dict['name']}'" if nt_dict else "this unknown note type"
        if aqt.utils.askUser(f"Are you sure you want to delete the addon-specific config for {nt_name}?"):
            self._lst.remove(prefs)
            wdgt.hide()
            self._lo.removeWidget(wdgt)


class StyleDialog(QDialog):
    def __init__(self, style_prefs: StylePrefs, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Note Type Style")
        self.setWindowModality(Qt.ApplicationModal)
        lo = QFormLayout(self)
        for item in ui_defs.style_defs:
            add_form_row(self, style_prefs, _DEFAULT_NT_PREFS.style, item, lo,
                         lambda n, v: f"CSS variable: {v}" if n == "tool" and v.startswith("--") else v)


class NoteTypeWidget(QFrame):
    def __init__(self, nt_prefs: NoteTypePrefs, parent: NoteTypesWidget):
        super().__init__(parent)

        style_dialog = StyleDialog(nt_prefs.style, self)

        top_lo = QHBoxLayout()

        delete_btn = QPushButton("Delete", self)
        delete_btn.setToolTip("Deletes the addon-specific preferences for this note type.\n"
                              "The actual note type will be unaffected.")
        delete_btn.clicked.connect(lambda: parent.remove(self, nt_prefs))

        top_lo.addWidget(delete_btn)
        nt_dict = aqt.mw.col.models.get(nt_prefs.nt_id)
        if nt_dict:
            lbl = QLabel(nt_dict["name"], self)
        else:
            lbl = QLabel("<i>Unknown note type</i>", self)
            lbl.setToolTip("This note type was probably deleted through the Anki interface "
                           "and you should also delete it here.\n"
                           "You can recover these preferences for another note type by manually editing "
                           "your config file and changing this entry's ID to an existing one.")
        top_lo.addWidget(lbl, 1)

        class UpdateType(Enum):
            REMOVE_MI = auto()
            SCRIPT = auto()
            STYLE = auto()

        def update(what: UpdateType):
            nt = aqt.mw.col.models.get(nt_prefs.nt_id)
            if not nt:
                aqt.utils.showWarning(f"Could not find note type in collection")
                return

            if what == UpdateType.STYLE:
                update_style(nt, nt_prefs.style, force=True)
            elif what == UpdateType.SCRIPT:
                update_script(nt, force=True)
            elif what == UpdateType.REMOVE_MI:
                remove_mia_migaku(nt)

            try:
                aqt.mw.col.models.update_dict(nt)
            except Exception as e:
                aqt.utils.showWarning(f"Updating the note type failed:\n{e}")

        remove_mi_btn = QPushButton("Remove MIA/Migaku", self)
        remove_mi_btn.setToolTip("Remove any CSS or JavaScript managed by the Migaku (formerly MIA) Japanese add-on\n"
                                 "from this note type's styling and templates")
        remove_mi_btn.clicked.connect(lambda: update(UpdateType.REMOVE_MI))
        top_lo.addWidget(remove_mi_btn)

        tt_shared = " regardless of the checkboxes below, adding it if it isn't present.\n" \
                    "Will overwrite any manual changes to the managed section immediately."

        script_btn = QPushButton("Update Script", self)
        script_btn.setToolTip("Update the script" + tt_shared)
        script_btn.clicked.connect(lambda: update(UpdateType.SCRIPT))
        top_lo.addWidget(script_btn)

        style_btn = QPushButton("Update Style", self)
        style_btn.setToolTip("Update the style according to the current (unsaved) preferences" + tt_shared)
        style_btn.clicked.connect(lambda: update(UpdateType.STYLE))
        top_lo.addWidget(style_btn)

        style_btn = QPushButton("Edit Style", self)
        style_btn.clicked.connect(lambda: style_dialog.show())
        top_lo.addWidget(style_btn)

        bottom_lo = QHBoxLayout()
        insert_checkboxes(ui_defs.nt_checkboxes, self, bottom_lo, nt_prefs, _DEFAULT_NT_PREFS)

        base_lo = QVBoxLayout(self)
        base_lo.addLayout(top_lo)
        base_lo.addLayout(bottom_lo)

        self.setFrameShape(QFrame.Box)


class PreferencesWidget(QTabWidget):
    def __init__(self, prefs: Prefs, parent: QWidget | None = None):
        super().__init__(parent)

        conv_wdgt = QWidget(self)

        conv_lo = QVBoxLayout()
        insert_checkboxes(ui_defs.conv_checkboxes, conv_wdgt, conv_lo, prefs, _DEFAULT_PREFS)
        conv_lo.addStretch()

        output_lo = QFormLayout()
        for item in ui_defs.output_defs:
            add_form_row(self, prefs.output, _DEFAULT_PREFS.output, item, output_lo)

        addon_lo = QFormLayout()
        for item in ui_defs.addon_defs:
            add_form_row(self, prefs.addon, _DEFAULT_PREFS.addon, item, addon_lo)

        output_addon_lo = QVBoxLayout()
        output_addon_lo.addLayout(output_lo)
        output_addon_lo.addLayout(addon_lo)

        default_ors = overrides.defaults()
        dor_widget = QWidget(self)

        dior_lo = QVBoxLayout()
        dior_lo.addWidget(QLabel("Default ignored words:", conv_wdgt))
        for dior in default_ors.ignore:
            dior_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.ignore, dior, conv_wdgt))
        dior_lo.addStretch()

        dwor_lo = QVBoxLayout()
        dwor_lo.addWidget(QLabel("Default word overrides:", conv_wdgt))
        for dwor in default_ors.word:
            dwor_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.word, dwor, conv_wdgt))
        dwor_lo.addStretch()

        daor_lo = QVBoxLayout()
        daor_lo.addWidget(QLabel("Default accent overrides:", conv_wdgt))
        for daor in default_ors.accent:
            daor_lo.addWidget(DefaultOverrideCheckbox(prefs.convert.disabled_override_ids.accent, daor, conv_wdgt))
        daor_lo.addStretch()

        dor_lo = QHBoxLayout(dor_widget)
        dor_lo.addLayout(dior_lo)
        dor_lo.addLayout(dwor_lo)
        dor_lo.addLayout(daor_lo)

        conv_dor_lo = QHBoxLayout(conv_wdgt)
        conv_dor_lo.addLayout(conv_lo)
        conv_dor_lo.addLayout(output_addon_lo, 1)

        self.addTab(conv_wdgt, "&General")
        self.addTab(dor_widget, "&Default Overrides")
        self.addTab(IgnoreOverrideWidget(prefs.convert.overrides.ignore, self), "&Ignored Words")
        self.addTab(WordOverrideWidget(prefs.convert.overrides.word, self), "&Word Overrides")
        self.addTab(AccentOverrideWidget(prefs.convert.overrides.accent, self), "&Accent Overrides")
        self.addTab(NoteTypesWidget(prefs.addon.note_types, self), "&Note Types")


class PreferencesDialog(QDialog):
    prefs: Prefs

    closed = pyqtSignal()

    def __init__(self, prefs: Prefs, parent: QWidget | None = None):
        super().__init__(parent)
        self.prefs = prefs

        self.setWindowTitle("Japanese Readings & Pitch Accent Add-on Preferences")
        self.setWindowModality(Qt.ApplicationModal)

        prefs_wdgt = PreferencesWidget(prefs, self)

        save_btn = QPushButton("Save", self)
        save_btn.clicked.connect(self.save)
        apply_btn = QPushButton("Apply", self)
        apply_btn.clicked.connect(self.apply)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.cancel)

        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        btn_lo.addWidget(save_btn)
        btn_lo.addWidget(apply_btn)
        btn_lo.addWidget(cancel_btn)

        main_lo = QVBoxLayout(self)
        main_lo.addWidget(prefs_wdgt)
        main_lo.addLayout(btn_lo)

    def apply(self):
        global_vars.update_prefs(deepcopy(self.prefs))
        global_vars.save_prefs()

    def save(self):
        self.apply()
        self.closed.emit()

    def cancel(self):
        if self.prefs != global_vars.prefs:
            resp = aqt.utils.askUser("Do you really want to close the preferences menu?\n"
                                     "All changes will be lost.", self)
            if not resp:
                return
        self.closed.emit()

    def reject(self) -> None:
        if self.prefs != global_vars.prefs:
            resp = aqt.utils.askUserDialog("Save changes to preferences?", ["Save", "Discard", "Cancel"], self).run()
            if resp == "Cancel":
                return
            elif resp == "Save":
                self.apply()
        super().reject()


def _remove_ui():
    aqt.mw.jrp_prefs_dialog.hide()
    del aqt.mw.jrp_prefs_dialog


def show_ui():
    prefs_copy = deepcopy(global_vars.prefs)
    aqt.mw.jrp_prefs_dialog = PreferencesDialog(prefs_copy, aqt.mw)
    aqt.mw.jrp_prefs_dialog.closed.connect(_remove_ui)
    aqt.mw.jrp_prefs_dialog.show()
