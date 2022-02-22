from collections.abc import Sequence
from typing import Iterable

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

import anki_ui_defs
import overrides
from overrides import DefaultOverride
from preferences import Prefs


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

        self._btn = QPushButton("Reset", self)
        sp = self._btn.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self._btn.setSizePolicy(sp)
        self._btn.clicked.connect(self.reset)

        self._cb = QCheckBox(label, self)
        self._cb.stateChanged.connect(self.state_change)
        self._cb.setChecked(_get(defaults, path))
        self.state_change(self._cb.isChecked())

        self._lo = QHBoxLayout(self)
        self._lo.setContentsMargins(0, 0, 0, 0)
        self._lo.addWidget(self._cb, 1)
        self._lo.addWidget(self._btn, 0)

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


class PreferencesWidget(QTabWidget):
    def __init__(self, prefs: Prefs, parent: QWidget | None = None):
        super().__init__(parent)
        defaults = Prefs()

        conv_wdgt = QWidget(self)

        conv_lo = QVBoxLayout()
        for item in anki_ui_defs.conv_checkboxes:
            if type(item) == str:
                conv_lo.addWidget(QLabel(item, conv_wdgt))
            else:
                conv_lo.addWidget(Checkbox(item["desc"], prefs, defaults, item["path"], conv_wdgt))
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
        conv_dor_lo.addLayout(conv_lo, 0)
        conv_dor_lo.addLayout(dor_lo, 1)

        self.addTab(conv_wdgt, "Conversion")
