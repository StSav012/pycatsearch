# -*- coding: utf-8 -*-
from __future__ import annotations

from math import inf
from typing import Callable

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QFormLayout, QTabWidget, QWidget

from .settings import Settings

__all__ = ["FrequencyBox"]


class FrequencySpinBox(QDoubleSpinBox):
    """`QDoubleSpinBox` with altered defaults"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setAccelerated(True)
        self.setDecimals(4)
        self.setMaximum(9999999.9999)
        self.setSuffix(self.tr(" MHz"))
        self.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.setKeyboardTracking(False)  # not to emit signals while typing


class FrequencyBox(QTabWidget):
    frequencyLimitsChanged: Signal = Signal(name="frequencyLimitsChanged")

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        from . import qta_icon  # import locally to avoid a circular import

        super().__init__(parent)

        self._settings: Settings = settings

        self._frequency_from: float = -inf  # [MHz]
        self._frequency_to: float = inf  # [MHz]
        self._frequency_center: float = 0.0  # [MHz]
        self._frequency_deviation: float = inf  # [MHz]

        self._page_by_range: QWidget = QWidget()
        self._layout_by_range: QFormLayout = QFormLayout(self._page_by_range)
        self._spin_frequency_from: FrequencySpinBox = FrequencySpinBox(self._page_by_range)
        self._spin_frequency_to: FrequencySpinBox = FrequencySpinBox(self._page_by_range)
        self._page_by_center: QWidget = QWidget()
        self._layout_by_center: QFormLayout = QFormLayout(self._page_by_center)
        self._spin_frequency_center: FrequencySpinBox = FrequencySpinBox(self._page_by_center)
        self._spin_frequency_deviation: FrequencySpinBox = FrequencySpinBox(self._page_by_center)

        self._layout_by_range.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self._spin_frequency_from.setValue(118747.341)
        self._layout_by_range.addRow(self.tr("From:"), self._spin_frequency_from)
        self._spin_frequency_to.setValue(118753.341)
        self._layout_by_range.addRow(self.tr("To:"), self._spin_frequency_to)
        self.addTab(self._page_by_range, qta_icon("mdi6.arrow-expand-horizontal"), self.tr("Range"))

        self._spin_frequency_center.setValue(118750.341)
        self._layout_by_center.addRow(self.tr("Center:"), self._spin_frequency_center)
        self._spin_frequency_deviation.setMaximum(99.9999)
        self._spin_frequency_deviation.setSingleStep(0.1)
        self._spin_frequency_deviation.setValue(0.4)
        self._layout_by_center.addRow(self.tr("Deviation:"), self._spin_frequency_deviation)
        self.addTab(self._page_by_center, qta_icon("mdi6.format-horizontal-align-center"), self.tr("Center"))

        self.load_settings()

        self._spin_frequency_from.valueChanged.connect(self._on_spin_frequency_from_edited)
        self._spin_frequency_to.valueChanged.connect(self._on_spin_frequency_to_edited)
        self._spin_frequency_center.valueChanged.connect(self._on_spin_frequency_center_edited)
        self._spin_frequency_deviation.valueChanged.connect(self._on_spin_frequency_deviation_edited)

    def load_settings(self) -> None:
        with self._settings.section("search"), self._settings.section("frequency"):
            self._frequency_from = self._settings.value("from", self._spin_frequency_from.value(), float)
            self._frequency_to = self._settings.value("to", self._spin_frequency_to.value(), float)
            self._frequency_center = self._settings.value("center", self._spin_frequency_center.value(), float)
            self._frequency_deviation = self._settings.value("deviation", self._spin_frequency_deviation.value(), float)

    def save_settings(self) -> None:
        with self._settings.section("search"), self._settings.section("frequency"):
            self._settings.setValue("from", self._frequency_from)
            self._settings.setValue("to", self._frequency_to)
            self._settings.setValue("center", self._frequency_center)
            self._settings.setValue("deviation", self._frequency_deviation)

    @property
    def min_frequency(self) -> float:
        if self.currentWidget() is self._page_by_range:
            return self._frequency_from
        else:
            return self._frequency_center - self._frequency_deviation

    @property
    def max_frequency(self) -> float:
        if self.currentWidget() is self._page_by_range:
            return self._frequency_to
        else:
            return self._frequency_center + self._frequency_deviation

    def set_frequency_limits(self, min_value: float, max_value: float) -> None:
        frequency_spins: list[QDoubleSpinBox] = [
            self._spin_frequency_from,
            self._spin_frequency_to,
            self._spin_frequency_center,
        ]
        min_value = self._settings.from_mhz(min_value)
        max_value = self._settings.from_mhz(max_value)
        spin: QDoubleSpinBox
        for spin in frequency_spins:
            spin.blockSignals(True)
            spin.setMinimum(min_value)
            spin.setMaximum(max_value)
            spin.blockSignals(False)

    @Slot(float)
    def _on_spin_frequency_from_edited(self, value: float) -> None:
        self._frequency_from = self._settings.to_mhz(value)
        self.frequencyLimitsChanged.emit()

    @Slot(float)
    def _on_spin_frequency_to_edited(self, value: float) -> None:
        self._frequency_to = self._settings.to_mhz(value)
        self.frequencyLimitsChanged.emit()

    @Slot(float)
    def _on_spin_frequency_center_edited(self, value: float) -> None:
        self._frequency_center = self._settings.to_mhz(value)
        self.frequencyLimitsChanged.emit()

    @Slot(float)
    def _on_spin_frequency_deviation_edited(self, value: float) -> None:
        self._frequency_deviation = self._settings.to_mhz(value)
        self.frequencyLimitsChanged.emit()

    def fill_parameters(self) -> None:
        frequency_suffix: int = self._settings.frequency_unit
        frequency_suffix_str: str = " " + self._settings.FREQUENCY_UNITS[frequency_suffix]
        from_mhz: Callable[[float], float] = self._settings.from_mhz
        if frequency_suffix in (0, 1, 2):  # MHz, GHz, cm⁻¹
            self._spin_frequency_from.setValue(from_mhz(self._frequency_from))
            self._spin_frequency_to.setValue(from_mhz(self._frequency_to))
            self._spin_frequency_center.setValue(from_mhz(self._frequency_center))
            self._spin_frequency_deviation.setValue(from_mhz(self._frequency_deviation))
        elif frequency_suffix == 3:  # nm
            self._spin_frequency_from.setValue(from_mhz(self._frequency_from))
            self._spin_frequency_to.setValue(from_mhz(self._frequency_to))
            self._spin_frequency_center.setValue(from_mhz(self._frequency_center))
            self._spin_frequency_deviation.setValue(
                abs(
                    from_mhz(self._frequency_center - self._frequency_deviation)
                    - from_mhz(self._frequency_center + self._frequency_deviation)
                )
                / 2.0
            )
        else:
            raise IndexError("Wrong frequency unit index", frequency_suffix)
        precision: int = [4, 7, 8, 8][frequency_suffix]
        step_factor: float = [2.5, 2.5, 2.5, 0.25][frequency_suffix]
        frequency_spins: list[QDoubleSpinBox] = [
            self._spin_frequency_from,
            self._spin_frequency_to,
            self._spin_frequency_center,
            self._spin_frequency_deviation,
        ]
        for spin in frequency_spins:
            spin.setSuffix(frequency_suffix_str)
            spin.setDecimals(precision)
            spin.setSingleStep(step_factor * self._spin_frequency_deviation.value())
