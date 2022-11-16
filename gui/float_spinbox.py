# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from typing import Final, Optional

from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDoubleSpinBox, QWidget

__all__ = ['FloatSpinBox']


class FloatSpinBox(QDoubleSpinBox):
    MODES: Final[list[str]] = ['auto', 'fixed', 'scientific']

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mode: str = 'auto'
        self._decimals: int = 2
        super().setDecimals(1000)

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, new_mode: str) -> None:
        if new_mode not in self.MODES:
            raise ValueError(f'Invalid mode: {new_mode}')
        self._mode = new_mode

    def valueFromText(self, text: str) -> float:
        return float(text.strip().split()[0])

    def textFromValue(self, v: float) -> str:
        if self._mode == 'auto':
            if abs(v) < self.singleStep() and v != 0.0:
                return f'{v:.{self._decimals}e}'
            else:
                return f'{v:.{self._decimals}f}'
        elif self._mode == 'fixed':
            return f'{v:.{self._decimals}f}'
        elif self._mode == 'scientific':
            return f'{v:.{self._decimals}e}'
        else:
            raise RuntimeError(f'Unknown mode {self._mode}')

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
        return ''

    def stepBy(self, steps: int) -> None:
        if self.value() != 0.0:
            exp: int = round(math.floor(math.log10(abs(self.value()))))
            self.setValue(self.value() + self.singleStep() * steps * 10.0 ** exp)
        else:
            self.setValue(self.singleStep() * steps)

    def decimals(self) -> int:
        return self._decimals

    def setDecimals(self, new_value: int) -> None:
        if new_value >= 0:
            self._decimals = new_value
        else:
            raise ValueError(f'Invalid decimals value: {new_value}')
