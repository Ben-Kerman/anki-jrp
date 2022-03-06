import os.path
from datetime import datetime
from enum import Enum
from typing import Iterable, List, Optional, Sequence, Tuple

import aqt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QPushButton, \
    QVBoxLayout, QWidget
from anki.errors import InvalidInput
from anki.models import NotetypeId
from anki.notes import Note, NoteId
from aqt.browser import Browser

from . import global_vars as gv
from ..pylib.conv_util import detect_syntax
from ..pylib.converter import convert
from ..pylib.html_processing import strip_html
from ..pylib.mecab import MecabError
from ..pylib.output import OutputType, fmt_jrp, fmt_migaku, insert_nbsp
from ..pylib.segments import ParsingError, Unit, parse_jrp, parse_migaku


class ConvType(Enum):
    DEFAULT = "Default"
    MIGAKU = "Migaku"
    REMOVE = "Remove"


def units_to_plain(lines: Iterable[Iterable[Unit]]) -> Iterable[str]:
    return ("".join(u.text() for u in units) for units in lines)


def convert_lines(lines: Iterable[str]) -> Optional[List[List[Unit]]]:
    try:
        return [convert(gv.mecab_handle.analyze(line), gv.prefs.convert, gv.dictionary) for line in lines]
    except MecabError as e:
        aqt.utils.showWarning(f"Mecab error, stopping conversion: {e}")
        return None


def write_backup_data(path: str, data: Sequence[Tuple[NoteId, str, str]]):
    def join_content(val: str) -> str:
        return "\n\t".join(val.splitlines())

    with open(path, "w", encoding="utf-8") as fd:
        for i, (note_id, old_val, new_val) in enumerate(data):
            if i > 0:
                fd.write("\n\n")
            fd.write(f"{note_id}\nold: {join_content(old_val)}\nnew: {join_content(new_val)}")


def convert_notes(brws: Browser, note_ids: Sequence[NoteId], field_idx: int,
                  conv_type: ConvType, regen: bool, backup: bool, dry_run: bool):
    failed_notes: List[NoteId] = []
    updated_notes: List[Note] = []
    backup_data: List[Tuple[NoteId, str, str]] = []

    for note_id in note_ids:
        note = brws.col.get_note(note_id)
        field = note.fields[field_idx]

        def update_note(new_val: str):
            if not dry_run:
                if backup:
                    backup_data.append((note_id, field, new_val))
                note.fields[field_idx] = new_val
                updated_notes.append(note)

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
                update_note(insert_nbsp("<br>".join(units_to_plain(line_units))))
                continue
            elif regen:
                line_units = convert_lines(units_to_plain(line_units))
        else:
            if conv_type == ConvType.REMOVE:
                continue
            line_units = convert_lines(lines)

        if line_units is None:
            return

        formatter = fmt_migaku if conv_type == ConvType.MIGAKU else fmt_jrp
        output_prefs = gv.prefs.output if regen else None
        update_note("<br>".join(formatter(units, output_prefs) for units in line_units))

    backup_msg = ""
    if backup:
        bu_filename = f"jrp-recovery-data_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.txt"
        backup_path = os.path.join(os.path.dirname(brws.col.path), bu_filename)
        if os.path.exists(backup_path):
            aqt.utils.showWarning(f"Backup file path already exists, aborting conversion: {backup_path}")
            return
        write_backup_data(backup_path, backup_data)
        backup_msg = f"\nRecovery file is located at: {backup_path}"

    if not dry_run:
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
                              "The failed notes remain unchanged and have been selected in the browser.\n"
                              "You can now convert them individually, or fix any issues "
                              f"and rerun the bulk conversion.{backup_msg}")
    else:
        aqt.utils.showInfo(f"Conversion successful.{backup_msg}")


class ConvertDialog(QDialog):
    _conv_type_cb: QComboBox
    _field_cb: QComboBox
    _gen_cb: QCheckBox
    _backup_cb: QCheckBox
    _dryrun_cb: QCheckBox

    def __init__(self, brws: Browser, nt_id: NotetypeId, notes: Sequence[NoteId], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Bulk Conversion")

        self._field_cb = QComboBox(self)
        # sort fields by position, just to be safe
        flds = [field["name"] for field in sorted(brws.col.models.get(nt_id)["flds"], key=lambda f: f["ord"])]
        self._field_cb.addItems(flds)
        self._field_cb.setToolTip("The field that will be converted.")
        self._conv_type_cb = QComboBox(self)
        self._conv_type_cb.addItems([ConvType.DEFAULT.value, ConvType.MIGAKU.value, ConvType.REMOVE.value])
        self._conv_type_cb.setToolTip("Which type of conversion to perform.\n"
                                      "The existing syntax type (if any) will be auto-detected.\n\n"
                                      "'Default' is the syntax specific to this add-on.\n"
                                      "'Migaku' is the more limited syntax from the Migaku Japanese Add-on,\n"
                                      "\twhich is based on that from the Japanese Support Add-on.\n"
                                      "'Remove' deletes either syntax if present")

        self._gen_cb = QCheckBox("Regenerate contents", self)
        self._gen_cb.setToolTip("If the conversion type is set to 'Default' or 'Migaku' and this is checked,\n"
                                "field contents will be fully regenerated for all notes.\n"
                                "By default, existing contents will be preserved as much as possible\n"
                                "and only notes without any syntax will be regenerated.\n"
                                "Has no effect with 'Remove'.")
        self._backup_cb = QCheckBox("Save emergency recovery data", self)
        self._backup_cb.setChecked(True)
        self._backup_cb.setToolTip("This will save a file containing each changed note's ID\n"
                                   "as well as the old and new contents of the target field\n"
                                   "in your collection's (profile's) directory.\n"
                                   "This is not a proper backup and you should export the deck(s)\n"
                                   "(with scheduling information) before running bulk conversions\n"
                                   "on very large amounts of notes.")
        self._dryrun_cb = QCheckBox("Dry run", self)
        self._dryrun_cb.setChecked(True)
        self._dryrun_cb.setToolTip("If this option is enabled, the conversion will run and show any errors "
                                   "that occur but changes won't be applied to the notes.\n"
                                   "Even when disabled, changes won't be written "
                                   "unless the whole conversion process succeeded without any general errors.\n"
                                   "Note-specific syntax errors will result in only that note being excluded "
                                   "and highlighted in the browser.")

        form_lo = QFormLayout()
        form_lo.addRow("Conversion type:", self._conv_type_cb)
        form_lo.addRow("Field:", self._field_cb)

        def exec_convert():
            convert_notes(brws, notes, self._field_cb.currentIndex(), ConvType(self._conv_type_cb.currentText()),
                          self._gen_cb.isChecked(), self._backup_cb.isChecked(), self._dryrun_cb.isChecked())
            self.accept()

        conv_btn = QPushButton("Convert", self)
        conv_btn.clicked.connect(lambda: exec_convert())
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(lambda: self.reject())

        btn_lo = QHBoxLayout()
        btn_lo.addStretch()
        btn_lo.addWidget(conv_btn)
        btn_lo.addWidget(cancel_btn)

        lo = QVBoxLayout(self)
        lo.addLayout(form_lo)
        lo.addWidget(self._gen_cb)
        lo.addWidget(self._backup_cb)
        lo.addWidget(self._dryrun_cb)
        lo.addLayout(btn_lo)


def insert_menu_items(brws: Browser):
    def set_up_dialog():
        note_ids = brws.selected_notes()
        if len(note_ids) < 2:
            aqt.utils.showWarning("Two or more notes need to be selected for bulk conversion.")
            return

        try:
            nt_id = brws.col.models.get_single_notetype_of_notes(note_ids)
        except InvalidInput:
            aqt.utils.showWarning("Only notes that all have the same note type can be converted in bulk.")
            return

        brws.jrp_conv_dialog = ConvertDialog(brws, nt_id, note_ids, brws)
        brws.jrp_conv_dialog.show()

    note_menu = brws.form.menu_Notes
    note_menu.addSeparator()
    bulk_conv_action = QAction("&JRP Add-on Bulk Conversion...", note_menu)
    bulk_conv_action.triggered.connect(set_up_dialog)
    note_menu.addAction(bulk_conv_action)
