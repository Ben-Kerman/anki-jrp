import os
import re
from typing import Any, Callable, Iterable, Optional, Sequence, TypeVar, Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QCheckBox, QColorDialog, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLayout, \
    QLineEdit, QPushButton, QSpinBox, QWidget

from . import util
from .prefs_ui_defs import WidgetType
from .util import get_path
from ..pylib.preferences import Prefs


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


class ResetButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(QIcon(util.get_asset_path("reset.svg")), "", parent)
        self.setFlat(True)
        sp = self.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp)
        self.setToolTip("Reset to default")


class Checkbox(QWidget):
    prefs: Prefs
    defaults: Prefs
    path: Sequence[str]

    _cb: QCheckBox
    _btn: QPushButton
    _lo: QHBoxLayout

    def __init__(self, label: str, prefs: Prefs, defaults: Prefs, path: Sequence[str],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.prefs = prefs
        self.defaults = defaults
        self.path = path

        self._btn = ResetButton(self)
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


def insert_checkboxes(defs: Iterable[Union[str, dict]], wdgt: QWidget, lo: QLayout, prefs: Any, defaults: Any):
    for item in defs:
        if type(item) == str:
            lo.addWidget(QLabel(item, wdgt))
        else:
            cb = Checkbox(item["desc"], prefs, defaults, item["path"], wdgt)
            if "tool" in item:
                cb.setToolTip(item["tool"])
            lo.addWidget(cb)


class PickerWidget(QWidget):
    _le: QLineEdit
    _picker: QDialog

    value_changed = pyqtSignal(str)

    def __init__(self, init_val: str, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._picker = self.setup_picker()

        self._le = QLineEdit(self)
        self._le.textEdited.connect(lambda txt: self.set_value(txt, True))

        btn = QPushButton("…", self)
        btn.setMaximumWidth(btn.fontMetrics().boundingRect("…").width() + 16)
        btn.clicked.connect(lambda: self._picker.show())

        lo = QHBoxLayout(self)
        lo.addWidget(self._le, 1)
        lo.addWidget(btn)
        lo.setContentsMargins(0, 0, 0, 0)

        self.set_value(init_val)

    def setup_picker(self) -> QDialog:
        raise NotImplementedError

    def set_value(self, val: str, from_text: bool = False) -> QDialog:
        raise NotImplementedError


class ColorWidget(PickerWidget):
    _picker: QColorDialog

    def setup_picker(self) -> QColorDialog:
        picker = QColorDialog(self)
        picker.colorSelected.connect(lambda qc: self.set_value(qc.name().lower()))
        return picker

    def set_value(self, val: str, from_text: bool = False):
        if not from_text:
            self._le.setText(val)
        if m := re.match(r"#([\da-f]{2})([\da-f]{2})([\da-f]{2})", val.strip(), re.I):
            qcolor = QColor(int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
        else:
            qcolor = QColor(0xff, 0xff, 0xff)
        self._picker.setCurrentColor(qcolor)
        self.value_changed.emit(val.strip())


class AnyFileWidget(PickerWidget):
    _picker: QFileDialog

    def setup_picker(self) -> QFileDialog:
        picker = QFileDialog(self)
        picker.fileSelected.connect(lambda path: self.set_value(path))
        return picker

    def set_value(self, val: str, from_text: bool = False):
        if not val:
            return

        new_val = get_path(val)
        self._picker.setDirectory(os.path.dirname(new_val))

        addon_dir = get_path()
        addon_drv, _ = os.path.splitdrive(addon_dir)
        val_drv, _ = os.path.splitdrive(new_val)
        if addon_drv.lower() == val_drv.lower():
            rel_path = os.path.relpath(new_val, addon_dir)
            if not rel_path.startswith(".."):
                new_val = rel_path

        if not from_text:
            self._le.setText(new_val)
        self.value_changed.emit(new_val)


class DirectoryWidget(AnyFileWidget):
    def setup_picker(self) -> QFileDialog:
        picker = super().setup_picker()
        picker.setFileMode(QFileDialog.Directory)
        return picker


class FileWidget(AnyFileWidget):
    def setup_picker(self) -> QFileDialog:
        picker = super().setup_picker()
        picker.setFileMode(QFileDialog.ExistingFile)
        return picker


T = TypeVar("T")


def add_form_row(parent: QWidget, prefs: T, defaults: T,
                 item: dict, form_lo: QFormLayout,
                 transform: Callable[[str, str], str] = lambda _, v: v):
    if type(item) == str:
        form_lo.addRow(QLabel(item))
        return

    def update_reset_btn(new_val: Any):
        if new_val == getattr(defaults, item["name"]):
            reset_btn.hide()
        else:
            reset_btn.show()

    def set_val(new_val: Any):
        setattr(prefs, item["name"], new_val)
        update_reset_btn(new_val)

    val = getattr(prefs, item["name"])
    if item["type"] == WidgetType.Checkbox:
        edit_wdgt = QCheckBox(parent)
        edit_wdgt.setChecked(val)
        edit_wdgt.clicked.connect(lambda s: set_val(bool(s)))
    elif item["type"] == WidgetType.Number:
        edit_wdgt = QSpinBox(parent)
        edit_wdgt.setValue(val)
        edit_wdgt.valueChanged.connect(set_val)
    elif item["type"] in [WidgetType.Color, WidgetType.Directory, WidgetType.File]:
        if item["type"] == WidgetType.Color:
            edit_wdgt = ColorWidget(val, parent)
        elif item["type"] == WidgetType.Directory:
            edit_wdgt = DirectoryWidget(val, parent)
        else:
            edit_wdgt = FileWidget(val, parent)
        edit_wdgt.value_changed.connect(set_val)
    elif item["type"] == WidgetType.Text:
        edit_wdgt = QLineEdit(val, parent)
        edit_wdgt.textEdited.connect(lambda v: set_val(v.strip()))
    else:
        raise Exception("invalid enum variant in UI definition")

    def reset_val():
        default_val = getattr(defaults, item["name"])
        set_val(default_val)
        if item["type"] == WidgetType.Checkbox:
            edit_wdgt.setChecked(default_val)
        elif item["type"] == WidgetType.Number:
            edit_wdgt.setValue(default_val)
        elif item["type"] in [WidgetType.Color, WidgetType.Directory, WidgetType.File]:
            edit_wdgt.set_value(default_val)
        elif item["type"] == WidgetType.Text:
            edit_wdgt.setText(default_val)
        else:
            raise Exception("invalid enum variant in UI definition")

    reset_btn = ResetButton(parent)
    reset_btn.clicked.connect(reset_val)
    update_reset_btn(val)

    edit_lo = QHBoxLayout()
    edit_lo.addWidget(reset_btn)
    edit_lo.addWidget(edit_wdgt)
    edit_lo.setAlignment(Qt.AlignLeft)

    lbl = QLabel(transform("desc", item["desc"]), parent)
    if "tool" in item:
        tt = transform("tool", item["tool"])
        lbl.setToolTip(tt)
        edit_wdgt.setToolTip(tt)

    form_lo.addRow(lbl, edit_lo)
