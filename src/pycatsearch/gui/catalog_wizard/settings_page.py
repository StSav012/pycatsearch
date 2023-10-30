# -*- coding: utf-8 -*-
from __future__ import annotations

from math import inf

from qtpy.QtWidgets import QDoubleSpinBox, QFormLayout, QWidget, QWizardPage

__all__ = ["SettingsPage"]


class SettingsPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setTitle(self.tr("New catalog"))

        layout: QFormLayout = QFormLayout(self)

        self._spin_min_frequency: QDoubleSpinBox = QDoubleSpinBox(self)
        self._spin_max_frequency: QDoubleSpinBox = QDoubleSpinBox(self)
        self._spin_min_frequency.setRange(0.0, inf)
        self._spin_max_frequency.setRange(0.0, inf)
        self._spin_min_frequency.valueChanged.connect(self._spin_max_frequency.setMinimum)
        self._spin_max_frequency.valueChanged.connect(self._spin_min_frequency.setMaximum)
        self._spin_min_frequency.setPrefix(self.tr("", "spin prefix"))
        self._spin_max_frequency.setPrefix(self.tr("", "spin prefix"))
        self._spin_min_frequency.setSuffix(self.tr(" MHz", "spin suffix"))
        self._spin_max_frequency.setSuffix(self.tr(" MHz", "spin suffix"))
        layout.addRow(self.tr("Minimal frequency:"), self._spin_min_frequency)
        layout.addRow(self.tr("Maximal frequency:"), self._spin_max_frequency)

        try:  # PyQt*
            self.registerField(
                "min_frequency", self._spin_min_frequency, "value", self._spin_min_frequency.valueChanged
            )
            self.registerField(
                "max_frequency", self._spin_max_frequency, "value", self._spin_max_frequency.valueChanged
            )
        except TypeError:  # PySide*
            from qtpy.QtCore import SIGNAL

            self.registerField(
                "min_frequency", self._spin_min_frequency, "value", SIGNAL("self._spin_min_frequency.valueChanged")
            )
            self.registerField(
                "max_frequency", self._spin_max_frequency, "value", SIGNAL("self._spin_max_frequency.valueChanged")
            )

    @property
    def frequency_limits(self) -> tuple[float, float]:
        return self._spin_min_frequency.value(), self._spin_max_frequency.value()

    @frequency_limits.setter
    def frequency_limits(self, new_limits: tuple[float, float]) -> None:
        min_frequency: float = min(new_limits)
        max_frequency: float = max(new_limits)
        self._spin_max_frequency.setMaximum(max(2.0 * max_frequency, self._spin_max_frequency.maximum()))
        if min_frequency > self._spin_max_frequency.value():
            self._spin_max_frequency.setValue(max_frequency)
            self._spin_min_frequency.setValue(min_frequency)
        else:
            self._spin_min_frequency.setValue(min_frequency)
            self._spin_max_frequency.setValue(max_frequency)

    def validatePage(self) -> bool:
        return self._spin_max_frequency.value() > self._spin_min_frequency.value()
