from collections.abc import Sequence
from typing import Iterable

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QTabWidget, QWidget

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

        self._cb = QCheckBox(label, self)
        self._cb.stateChanged.connect(self.state_change)

        self._btn = QPushButton("Reset", self)
        self._btn.hide()
        self._btn.clicked.connect(self.reset)

        self._lo = QHBoxLayout(self)
        self._lo.addWidget(self._cb)
        self._lo.addWidget(self._btn)
        self._lo.addStretch()

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


class PreferencesWidget(QTabWidget):
    def __init__(self, prefs: Prefs):
        super().__init__()
        defaults = Prefs()
