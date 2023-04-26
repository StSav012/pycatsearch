# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Callable, Final

from qtpy.QtCore import QSettings

from ..utils import *

__all__ = ['Settings']


class Settings(QSettings):
    """ convenient internal representation of the application settings """
    FREQUENCY_UNITS: Final[list[str]] = ['MHz', 'GHz', 'cm⁻¹', 'nm']
    INTENSITY_UNITS: Final[list[str]] = ['lg(nm² × MHz)', 'nm² × MHz', 'lg(cm / molecule)', 'cm / molecule']
    ENERGY_UNITS: Final[list[str]] = ['cm⁻¹', 'meV', 'J']
    TEMPERATURE_UNITS: Final[list[str]] = ['K', '°C']
    LINE_ENDS: Final[list[str]] = [r'Line Feed (\n)', r'Carriage Return (\r)', r'CR+LF (\r\n)', r'LF+CR (\n\r)']
    _LINE_ENDS: Final[list[str]] = ['\n', '\r', '\r\n', '\n\r']
    CSV_SEPARATORS: Final[list[str]] = [r'comma (,)', r'tab (\t)', r'semicolon (;)', r'space ( )']
    _CSV_SEPARATORS: Final[list[str]] = [',', '\t', ';', ' ']

    DIALOG: dict[str, dict[str, tuple[Any, ...]]] = {
        'Start': {
            'Load catalogs when the program starts': ('load_last_catalogs',),
        },
        'Display': {
            'Allow rich text in formulas': ('rich_text_in_formulas',),
        },
        'Search': {
            'Timeout:': (slice(1, 99), (' sec',), 'timeout',),
        },
        'Units': {
            'Frequency:': (FREQUENCY_UNITS, 'frequency_unit'),
            'Intensity:': (INTENSITY_UNITS, 'intensity_unit'),
            'Energy:': (ENERGY_UNITS, 'energy_unit'),
            'Temperature:': (TEMPERATURE_UNITS, 'temperature_unit'),
        },
        'Export': {
            'With units': ('with_units',),
            'Line ending:': (LINE_ENDS, _LINE_ENDS, 'line_end'),
            'CSV separator:': (CSV_SEPARATORS, _CSV_SEPARATORS, 'csv_separator'),
        }
    }

    TO_MHZ: Final[list[Callable[[float], float]]] = [lambda x: x, ghz_to_mhz, rec_cm_to_mhz, nm_to_mhz]
    FROM_MHZ: Final[list[Callable[[float], float]]] = [lambda x: x, mhz_to_ghz, mhz_to_rec_cm, mhz_to_nm]

    TO_LOG10_SQ_NM_MHZ: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        sq_nm_mhz_to_log10_sq_nm_mhz,
        log10_cm_per_molecule_to_log10_sq_nm_mhz,
        cm_per_molecule_to_log10_sq_nm_mhz
    ]
    FROM_LOG10_SQ_NM_MHZ: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        log10_sq_nm_mhz_to_sq_nm_mhz,
        log10_sq_nm_mhz_to_log10_cm_per_molecule,
        log10_sq_nm_mhz_to_cm_per_molecule
    ]

    TO_REC_CM: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        meV_to_rec_cm,
        j_to_rec_cm
    ]
    FROM_REC_CM: Final[list[Callable[[float], float]]] = [
        lambda x: x,
        rec_cm_to_meV,
        rec_cm_to_j
    ]

    TO_K: Final[list[Callable[[float], float]]] = [lambda x: x, lambda x: x + 273.15]
    FROM_K: Final[list[Callable[[float], float]]] = [lambda x: x, lambda x: x - 273.15]

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    @property
    def frequency_unit(self) -> int:
        self.beginGroup('frequency')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return v

    @frequency_unit.setter
    def frequency_unit(self, new_value: int | str) -> None:
        self.beginGroup('frequency')
        if isinstance(new_value, str):
            new_value = self.FREQUENCY_UNITS.index(new_value)
        self.setValue('unit', new_value)
        self.endGroup()

    @property
    def frequency_unit_str(self) -> str:
        self.beginGroup('frequency')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.FREQUENCY_UNITS[v]

    @property
    def to_mhz(self) -> Callable[[float], float]:
        self.beginGroup('frequency')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.TO_MHZ[v]

    @property
    def from_mhz(self) -> Callable[[float], float]:
        self.beginGroup('frequency')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.FROM_MHZ[v]

    @property
    def intensity_unit(self) -> int:
        self.beginGroup('intensity')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return v

    @intensity_unit.setter
    def intensity_unit(self, new_value: int | str) -> None:
        self.beginGroup('intensity')
        if isinstance(new_value, str):
            new_value = self.INTENSITY_UNITS.index(new_value)
        self.setValue('unit', new_value)
        self.endGroup()

    @property
    def intensity_unit_str(self) -> str:
        self.beginGroup('intensity')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.INTENSITY_UNITS[v]

    @property
    def to_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        self.beginGroup('intensity')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.TO_LOG10_SQ_NM_MHZ[v]

    @property
    def from_log10_sq_nm_mhz(self) -> Callable[[float], float]:
        self.beginGroup('intensity')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.FROM_LOG10_SQ_NM_MHZ[v]

    @property
    def energy_unit(self) -> int:
        self.beginGroup('energy')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return v

    @energy_unit.setter
    def energy_unit(self, new_value: int | str) -> None:
        self.beginGroup('energy')
        if isinstance(new_value, str):
            new_value = self.ENERGY_UNITS.index(new_value)
        self.setValue('unit', new_value)
        self.endGroup()

    @property
    def energy_unit_str(self) -> str:
        self.beginGroup('energy')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.ENERGY_UNITS[v]

    @property
    def to_rec_cm(self) -> Callable[[float], float]:
        self.beginGroup('energy')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.TO_REC_CM[v]

    @property
    def from_rec_cm(self) -> Callable[[float], float]:
        self.beginGroup('energy')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.FROM_REC_CM[v]

    @property
    def temperature_unit(self) -> int:
        self.beginGroup('temperature')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return v

    @temperature_unit.setter
    def temperature_unit(self, new_value: int | str) -> None:
        self.beginGroup('temperature')
        if isinstance(new_value, str):
            new_value = self.TEMPERATURE_UNITS.index(new_value)
        self.setValue('unit', new_value)
        self.endGroup()

    @property
    def temperature_unit_str(self) -> str:
        self.beginGroup('temperature')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.TEMPERATURE_UNITS[v]

    @property
    def to_k(self) -> Callable[[float], float]:
        self.beginGroup('temperature')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.TO_K[v]

    @property
    def from_k(self) -> Callable[[float], float]:
        self.beginGroup('temperature')
        v: int = self.value('unit', 0, int)
        self.endGroup()
        return self.FROM_K[v]

    @property
    def load_last_catalogs(self) -> bool:
        self.beginGroup('start')
        v: bool = self.value('loadLastCatalogs', True, bool)
        self.endGroup()
        return v

    @load_last_catalogs.setter
    def load_last_catalogs(self, new_value: bool) -> None:
        self.beginGroup('start')
        self.setValue('loadLastCatalogs', new_value)
        self.endGroup()

    @property
    def rich_text_in_formulas(self) -> bool:
        self.beginGroup('display')
        v: bool = self.value('richTextInFormulas', True, bool)
        self.endGroup()
        return v

    @rich_text_in_formulas.setter
    def rich_text_in_formulas(self, new_value: bool) -> None:
        self.beginGroup('display')
        self.setValue('richTextInFormulas', new_value)
        self.endGroup()

    @property
    def line_end(self) -> str:
        self.beginGroup('export')
        v: int = self.value('lineEnd', self._LINE_ENDS.index(os.linesep), int)
        self.endGroup()
        return self._LINE_ENDS[v]

    @line_end.setter
    def line_end(self, new_value: str) -> None:
        self.beginGroup('export')
        self.setValue('lineEnd', self._LINE_ENDS.index(new_value))
        self.endGroup()

    @property
    def csv_separator(self) -> str:
        self.beginGroup('export')
        v: int = self.value('csvSeparator', self._CSV_SEPARATORS.index('\t'), int)
        self.endGroup()
        return self._CSV_SEPARATORS[v]

    @csv_separator.setter
    def csv_separator(self, new_value: str) -> None:
        self.beginGroup('export')
        self.setValue('csvSeparator', self._CSV_SEPARATORS.index(new_value))
        self.endGroup()

    @property
    def with_units(self) -> bool:
        self.beginGroup('export')
        v: bool = self.value('withUnits', True, bool)
        self.endGroup()
        return v

    @with_units.setter
    def with_units(self, new_value: bool) -> None:
        self.beginGroup('export')
        self.setValue('withUnits', new_value)
        self.endGroup()

    @property
    def timeout(self) -> float:
        self.beginGroup('search')
        v: float = self.value('timeout', 99.0, float)
        self.endGroup()
        return v

    @timeout.setter
    def timeout(self, new_value: float) -> None:
        self.beginGroup('search')
        self.setValue('timeout', new_value)
        self.endGroup()
