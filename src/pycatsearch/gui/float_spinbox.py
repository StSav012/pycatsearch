# -*- coding: utf-8 -*-
from __future__ import annotations

import enum
from math import floor, log10

from qtpy.QtCore import QLocale
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDoubleSpinBox, QWidget

__all__ = ["FloatSpinBox"]


class FloatSpinBox(QDoubleSpinBox):
    class Mode(enum.Enum):
        auto = enum.auto()
        fixed = enum.auto()
        scientific = enum.auto()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode: FloatSpinBox.Mode = FloatSpinBox.Mode.auto
        self._decimals: int = 2
        super().setDecimals(1000)

    @property
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, new_mode: "FloatSpinBox.Mode") -> None:
        if not isinstance(new_mode, FloatSpinBox.Mode):
            raise TypeError(f"Invalid mode: {new_mode}")
        self._mode = new_mode

    def valueFromText(self, text: str) -> float:
        locale: QLocale = QLocale()
        value: float
        ok: bool
        value, ok = locale.toDouble(text[len(self.prefix()) : -len(self.suffix())])
        if not ok:
            raise ValueError(f"could not convert string to float: {text[len(self.prefix()):-len(self.suffix())]!r}")
        return value

    def textFromValue(self, v: float) -> str:
        locale: QLocale = QLocale()
        decimal_point: str = locale.decimalPoint()
        if self._mode == FloatSpinBox.Mode.auto:
            if abs(v) < self.singleStep() and v != 0.0:
                return f"{v:.{self._decimals}e}".replace(".", decimal_point)
            else:
                return f"{v:.{self._decimals}f}".replace(".", decimal_point)
        elif self._mode == FloatSpinBox.Mode.fixed:
            return f"{v:.{self._decimals}f}".replace(".", decimal_point)
        elif self._mode == FloatSpinBox.Mode.scientific:
            return f"{v:.{self._decimals}e}".replace(".", decimal_point)
        else:
            raise RuntimeError(f"Unknown mode {self._mode}")

    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:
        try:
            self.valueFromText(text)
        except (ValueError, TypeError):
            return QValidator.State.Invalid, text, pos
        else:
            return QValidator.State.Acceptable, text, pos

    def fixup(self, text: str) -> str:
        for word in text.split():
            try:
                float(word)
            except ValueError:
                continue
            else:
                return word
        return ""

    def stepBy(self, steps: int) -> None:
        if self.value() != 0.0:
            exp: int = round(floor(log10(abs(self.value()))))
            self.setValue(self.value() + self.singleStep() * steps * 10.0**exp)
        else:
            self.setValue(self.singleStep() * steps)

    def decimals(self) -> int:
        return self._decimals

    def setDecimals(self, new_value: int) -> None:
        if new_value >= 0:
            self._decimals = new_value
        else:
            raise ValueError(f"Invalid decimals value: {new_value}")
