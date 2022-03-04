from enum import Enum

import aqt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QMenu, QPushButton, \
    QVBoxLayout, QWidget
from anki.notes import NoteId
from aqt.browser import Browser


class ConvType(Enum):
    DEFAULT = "Default"
    MIGAKU = "Migaku"
    REMOVE = "Remove"


def convert_notes(brws: Browser, conv_type: ConvType, regen: bool, dry_run: bool):
    failed_notes: list[NoteId] = []

    for note_id in brws.selected_notes():
        pass

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

    def __init__(self, brws: Browser, parent: QWidget | None = None):
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
            convert_notes(brws, self._conv_type_cb.currentText(),
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
        brws.jrp_conv_dialog = ConvertDialog(brws, brws)
        brws.jrp_conv_dialog.show()

    syn_conv_action = QAction("&Change Syntax", addon_menu)
    syn_conv_action.triggered.connect(set_up_dialog)

    addon_menu.addAction(syn_conv_action)
    note_menu.addMenu(addon_menu)
