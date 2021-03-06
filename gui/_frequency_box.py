# -*- coding: utf-8 -*-
import math
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QFormLayout, QTabWidget, \
    QWidget

from gui._settings import Settings
from utils import *

__all__ = ['FrequencyBox']


class FrequencyBox(QTabWidget):
    def __init__(self, settings: Settings, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._settings: Settings = settings

        self._frequency_from: float = -math.inf  # [MHz]
        self._frequency_to: float = math.inf  # [MHz]
        self._frequency_center: float = 0.0  # [MHz]
        self._frequency_deviation: float = math.inf  # [MHz]

        self._page_by_range: QWidget = QWidget()
        self._layout_by_range: QFormLayout = QFormLayout(self._page_by_range)
        self._spin_frequency_from: QDoubleSpinBox = QDoubleSpinBox(self._page_by_range)
        self._spin_frequency_to: QDoubleSpinBox = QDoubleSpinBox(self._page_by_range)
        self._page_by_center: QWidget = QWidget()
        self._layout_by_center: QFormLayout = QFormLayout(self._page_by_center)
        self._spin_frequency_center: QDoubleSpinBox = QDoubleSpinBox(self._page_by_center)
        self._spin_frequency_deviation: QDoubleSpinBox = QDoubleSpinBox(self._page_by_center)

        self._layout_by_range.setLabelAlignment(Qt.AlignLeft)
        self._spin_frequency_from.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self._spin_frequency_from.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._spin_frequency_from.setAccelerated(True)
        self._spin_frequency_from.setDecimals(4)
        self._spin_frequency_from.setMaximum(9999999.9999)
        self._spin_frequency_from.setValue(118747.341)
        self._spin_frequency_from.setSuffix(self._spin_frequency_from.tr(' MHz'))
        self._layout_by_range.addRow(self._layout_by_range.tr('From:'), self._spin_frequency_from)
        self._spin_frequency_to.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self._spin_frequency_to.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._spin_frequency_to.setAccelerated(True)
        self._spin_frequency_to.setDecimals(4)
        self._spin_frequency_to.setMaximum(9999999.9999)
        self._spin_frequency_to.setValue(118753.341)
        self._spin_frequency_to.setSuffix(self._spin_frequency_to.tr(' MHz'))
        self._layout_by_range.addRow(self._layout_by_range.tr('To:'), self._spin_frequency_to)
        self.addTab(self._page_by_range, self.tr('Range'))

        self._spin_frequency_center.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self._spin_frequency_center.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._spin_frequency_center.setAccelerated(True)
        self._spin_frequency_center.setDecimals(4)
        self._spin_frequency_center.setMaximum(9999999.9999)
        self._spin_frequency_center.setValue(118750.341)
        self._spin_frequency_center.setSuffix(self._spin_frequency_center.tr(' MHz'))
        self._layout_by_center.addRow(self._layout_by_center.tr('Center:'), self._spin_frequency_center)
        self._spin_frequency_deviation.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self._spin_frequency_deviation.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._spin_frequency_deviation.setDecimals(4)
        self._spin_frequency_deviation.setMaximum(99.9999)
        self._spin_frequency_deviation.setSingleStep(0.1)
        self._spin_frequency_deviation.setValue(0.4)
        self._spin_frequency_deviation.setSuffix(self._spin_frequency_deviation.tr(' MHz'))
        self._layout_by_center.addRow(self._layout_by_center.tr('Deviation:'), self._spin_frequency_deviation)
        self.addTab(self._page_by_center, self.tr('Center'))

        self.load_settings()

        self._spin_frequency_from.editingFinished.connect(self.on_spin_frequency_from_edited)
        self._spin_frequency_to.editingFinished.connect(self.on_spin_frequency_to_edited)
        self._spin_frequency_center.editingFinished.connect(self.on_spin_frequency_center_edited)
        self._spin_frequency_deviation.editingFinished.connect(self.on_spin_frequency_deviation_edited)

    def load_settings(self):
        self._settings.beginGroup('search')
        self._settings.beginGroup('frequency')
        self._frequency_from = self._settings.value('from', self._spin_frequency_from.value(), float)
        self._frequency_to = self._settings.value('to', self._spin_frequency_to.value(), float)
        self._frequency_center = self._settings.value('center', self._spin_frequency_center.value(), float)
        self._frequency_deviation = self._settings.value('deviation', self._spin_frequency_deviation.value(), float)
        self._settings.endGroup()
        self._settings.endGroup()

    def save_settings(self):
        self._settings.beginGroup('search')
        self._settings.beginGroup('frequency')
        self._settings.setValue('from', self._frequency_from)
        self._settings.setValue('to', self._frequency_to)
        self._settings.setValue('center', self._frequency_center)
        self._settings.setValue('deviation', self._frequency_deviation)
        self._settings.endGroup()
        self._settings.endGroup()

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

    def set_frequency_limits(self, min_value: float, max_value: float):
        frequency_spins: List[QDoubleSpinBox] = [self._spin_frequency_from, self._spin_frequency_to,
                                                 self._spin_frequency_center]
        min_value = self._settings.from_mhz(min_value)
        max_value = self._settings.from_mhz(max_value)
        for spin in frequency_spins:
            spin.setMinimum(min_value)
            spin.setMaximum(max_value)

    def on_spin_frequency_from_edited(self):
        self._frequency_from = self._settings.to_mhz(self._spin_frequency_from.value())

    def on_spin_frequency_to_edited(self):
        self._frequency_to = self._settings.to_mhz(self._spin_frequency_to.value())

    def on_spin_frequency_center_edited(self):
        self._frequency_center = self._settings.to_mhz(self._spin_frequency_center.value())

    def on_spin_frequency_deviation_edited(self):
        self._frequency_deviation = self._settings.to_mhz(self._spin_frequency_deviation.value())

    def fill_parameters(self):
        frequency_suffix: int = self._settings.frequency_unit
        frequency_suffix_str: str = ' ' + self._settings.FREQUENCY_UNITS[frequency_suffix]
        if frequency_suffix in (0, 1, 2):  # MHz, GHz, cm⁻¹
            self._spin_frequency_from.setValue(self._settings.from_mhz(self._frequency_from))
            self._spin_frequency_to.setValue(self._settings.from_mhz(self._frequency_to))
            self._spin_frequency_center.setValue(self._settings.from_mhz(self._frequency_center))
            self._spin_frequency_deviation.setValue(self._settings.from_mhz(self._frequency_deviation))
        elif frequency_suffix == 3:  # nm
            self._spin_frequency_from.setValue(mhz_to_nm(self._frequency_from))
            self._spin_frequency_to.setValue(mhz_to_nm(self._frequency_to))
            self._spin_frequency_center.setValue(mhz_to_nm(self._frequency_center))
            self._spin_frequency_deviation.setValue(
                abs(mhz_to_nm(self._frequency_center - self._frequency_deviation) -
                    mhz_to_nm(self._frequency_center + self._frequency_deviation)) / 2.0)
        else:
            raise IndexError('Wrong frequency unit index', frequency_suffix)
        precision: int = [4, 7, 8, 8][frequency_suffix]
        step_factor: float = [2.5, 2.5, 2.5, 0.25][frequency_suffix]
        frequency_spins: List[QDoubleSpinBox] = [self._spin_frequency_from, self._spin_frequency_to,
                                                 self._spin_frequency_center, self._spin_frequency_deviation]
        for spin in frequency_spins:
            spin.setSuffix(frequency_suffix_str)
            spin.setDecimals(precision)
            spin.setSingleStep(step_factor * self._spin_frequency_deviation.value())
