from enum import Enum
from typing import Iterable

import aqt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QMenu, QPushButton, \
    QVBoxLayout, QWidget
from anki.notes import Note, NoteId
from aqt.browser import Browser

from . import global_vars as gv
from .editor import OutputType, detect_syntax
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import MecabError
from ..pylib.output import fmt_jrp, fmt_migaku
from ..pylib.segments import ParsingError, Unit, parse_jrp, parse_migaku


class ConvType(Enum):
    DEFAULT = "Default"
    MIGAKU = "Migaku"
    REMOVE = "Remove"


def units_to_plain(lines: Iterable[Iterable[Unit]]) -> Iterable[str]:
    return ("".join(u.text() for u in units) for units in lines)


def convert_lines(lines: Iterable[str]) -> list[list[Unit]] | None:
    try:
        return [convert(line, gv.prefs.convert, gv.mecab_handle, gv.dictionary) for line in lines]
    except MecabError as e:
        aqt.utils.showWarning(f"Mecab error, stopping conversion: {e}")
        return None


def convert_notes(brws: Browser, note_ids: list[NoteId], conv_type: ConvType, regen: bool, dry_run: bool):
    field_idx = 0  # TODO
    failed_notes: list[NoteId] = []
    updated_notes: list[Note] = []

    for note_id in note_ids:
        note = brws.col.get_note(note_id)

        def update_note(new_val: str):
            if not dry_run:
                note.fields[field_idx] = new_val
                updated_notes.append(note)

        field = note.fields[field_idx]
        lines = strip_html(field)
        existing_type = detect_syntax(field)
        if existing_type:
            parser = parse_migaku if existing_type == OutputType.MIGAKU else parse_jrp
            try:
                line_units = [parser(line) for line in lines]
            except ParsingError:
                failed_notes.append(note_id)
                continue

            if conv_type == ConvType.REMOVE:
                update_note("<br>".join(units_to_plain(line_units)))
        else:
            if conv_type == ConvType.REMOVE:
                continue
            line_units = convert_lines(lines)

        if regen and existing_type:
            line_units = convert_lines(units_to_plain(line_units))

        if not line_units:
            return

        formatter = fmt_migaku if conv_type == ConvType.MIGAKU else fmt_jrp
        update_note("<br>".join(formatter(units) for units in line_units))

    undo_step = brws.col.add_custom_undo_entry("Bulk conversion")
    brws.col.update_notes(updated_notes)
    brws.col.merge_undo_entries(undo_step)

    if failed_notes:
        brws.search_for(f"nid:{','.join(map(str, failed_notes))}")
        if dry_run:
            cond_msg = "Since this was a dry run no notes have been updated."
        else:
            cond_msg = "All other selected notes were updated successfully."
        aqt.utils.showWarning(f"Conversion failed for some notes. {cond_msg}\n"
                              f"The failed notes remain unchanged and have been selected in the browser.\n"
                              "You can now convert them individually or fix any issues "
                              "and rerun the bulk conversion.")
    else:
        aqt.utils.showInfo("Conversion successful.")


class ConvertDialog(QDialog):
    _conv_type_cb: QComboBox
    _gen_cb: QCheckBox
    _dryrun_cb: QCheckBox

    def __init__(self, brws: Browser, notes: list[NoteId], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)

        lo = QVBoxLayout(self)

        conv_lo = QHBoxLayout()
        self._conv_type_cb = QComboBox(self)
        self._conv_type_cb.addItems([ConvType.DEFAULT.value, ConvType.MIGAKU.value, ConvType.REMOVE.value])
        lbl = QLabel("Conversion type:")
        conv_lo.addWidget(lbl, 1)
        conv_lo.addWidget(self._conv_type_cb)
        lo.addLayout(conv_lo)

        self._gen_cb = QCheckBox("(Re)generate contents", self)
        lo.addWidget(self._gen_cb)

        self._dryrun_cb = QCheckBox("Dry run", self)
        self._dryrun_cb.setChecked(True)
        lo.addWidget(self._dryrun_cb)

        def exec_convert():
            convert_notes(brws, notes, self._conv_type_cb.currentText(),
                          self._gen_cb.isChecked(), self._dryrun_cb.isChecked())
            self.accept()

        conv_btn = QPushButton("Convert", self)
        conv_btn.clicked.connect(lambda: exec_convert())
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(lambda: self.reject())
        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        btn_lo.addWidget(conv_btn)
        btn_lo.addWidget(cancel_btn)

        lo.addLayout(btn_lo)


def insert_menu_items(brws: Browser):
    note_menu = brws.form.menu_Notes
    note_menu.addSeparator()
    addon_menu = QMenu("&Japanese Readings && Accent Add-on", note_menu)

    def set_up_dialog():
        note_ids = brws.selected_notes()

        brws.jrp_conv_dialog = ConvertDialog(brws, note_ids, brws)
        brws.jrp_conv_dialog.show()

    syn_conv_action = QAction("&Change Syntax", addon_menu)
    syn_conv_action.triggered.connect(set_up_dialog)

    addon_menu.addAction(syn_conv_action)
    note_menu.addMenu(addon_menu)
