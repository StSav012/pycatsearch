# -*- coding: utf-8 -*-
from __future__ import annotations

import enum
from typing import Callable, Final

from qtpy.QtCore import QAbstractTableModel, QLocale, QModelIndex, QPersistentModelIndex, Qt
from qtpy.QtWidgets import QWidget

from .settings import Settings
from ..catalog import CatalogType
from ..utils import FREQUENCY, INTENSITY, LINES, LOWER_STATE_ENERGY, best_name

__all__ = ["FoundLinesModel"]


class FoundLinesModel(QAbstractTableModel):
    ROW_BATCH_COUNT: Final[int] = 5

    class DataType:
        __slots__ = [
            "species_tag",
            "name",
            "frequency_str",
            "frequency",
            "intensity_str",
            "intensity",
            "lower_state_energy_str",
            "lower_state_energy",
        ]

        def __init__(
            self,
            species_tag: int,
            name: str,
            frequency_str: str,
            frequency: float,
            intensity_str: str,
            intensity: float,
            lower_state_energy_str: str,
            lower_state_energy: float,
        ) -> None:
            self.species_tag: int = species_tag
            self.name: str = name
            self.frequency_str: str = frequency_str
            self.frequency: float = frequency
            self.intensity_str: str = intensity_str
            self.intensity: float = intensity
            self.lower_state_energy_str: str = lower_state_energy_str
            self.lower_state_energy: float = lower_state_energy

        def __eq__(self, other: "FoundLinesModel.DataType") -> int:
            if not isinstance(other, FoundLinesModel.DataType):
                return NotImplemented
            return (
                self.species_tag == other.species_tag
                and self.frequency == other.frequency
                and self.intensity == other.intensity
                and self.lower_state_energy == other.lower_state_energy
            )

        def __hash__(self) -> int:
            return hash(self.species_tag) ^ hash(self.frequency) ^ hash(self.lower_state_energy)

    class Columns(enum.IntEnum):
        SubstanceName = 0
        Frequency = 1
        Intensity = 2
        LowerStateEnergy = 3

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings: Settings = settings
        self._data: list[FoundLinesModel.DataType] = []
        self._rows_loaded: int = FoundLinesModel.ROW_BATCH_COUNT

        unit_format: Final[str] = self.tr("{value} [{unit}]", "unit format")
        self._header: Final[list[str]] = [
            self.tr("Substance"),
            unit_format.format(value=self.tr("Frequency"), unit=self._settings.frequency_unit_str),
            unit_format.format(value=self.tr("Intensity"), unit=self._settings.intensity_unit_str),
            unit_format.format(value=self.tr("Lower state energy"), unit=self._settings.energy_unit_str),
        ]

    def update_units(self) -> None:
        unit_format: Final[str] = self.tr("{value} [{unit}]", "unit format")
        self._header[FoundLinesModel.Columns.Frequency] = unit_format.format(
            value=self.tr("Frequency"),
            unit=self._settings.frequency_unit_str,
        )
        self._header[FoundLinesModel.Columns.Intensity] = unit_format.format(
            value=self.tr("Intensity"),
            unit=self._settings.intensity_unit_str,
        )
        self._header[FoundLinesModel.Columns.LowerStateEnergy] = unit_format.format(
            value=self.tr("Lower state energy"),
            unit=self._settings.energy_unit_str,
        )

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = ...) -> int:
        return min(len(self._data), self._rows_loaded)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = ...) -> int:
        return len(self._header)

    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                item: FoundLinesModel.DataType = self._data[index.row()]
                column_index: int = index.column()
                if column_index == FoundLinesModel.Columns.SubstanceName:
                    return item.name
                if column_index == FoundLinesModel.Columns.Frequency:
                    return item.frequency_str
                if column_index == FoundLinesModel.Columns.Intensity:
                    return item.intensity_str
                if column_index == FoundLinesModel.Columns.LowerStateEnergy:
                    return item.lower_state_energy_str
        return None

    def row(self, row_index: int) -> DataType:
        return self._data[row_index]

    def headerData(self, col: int, orientation: Qt.Orientation, role: int = ...) -> str | None:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._header[col]
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: str, role: int = ...) -> bool:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self._header)
        ):
            self._header[section] = value
            return True
        return False

    def clear(self) -> None:
        self.set_entries(dict())

    def set_entries(self, entries: CatalogType) -> None:
        from_mhz: Callable[[float], float] = self._settings.from_mhz
        from_log10_sq_nm_mhz: Callable[[float], float] = self._settings.from_log10_sq_nm_mhz
        from_rec_cm: Callable[[float], float] = self._settings.from_rec_cm
        frequency_suffix: int = self._settings.frequency_unit
        precision: int = [4, 7, 8, 8][frequency_suffix]
        locale: QLocale = QLocale()
        decimal_point: str = locale.decimalPoint()

        def frequency_str(frequency: float) -> tuple[str, float]:
            frequency = from_mhz(frequency)
            return f"{frequency:.{precision}f}".replace(".", decimal_point), frequency

        def intensity_str(intensity: float) -> tuple[str, float]:
            intensity = from_log10_sq_nm_mhz(intensity)
            if intensity == 0.0:
                return "0", intensity
            elif abs(intensity) < 0.1:
                return f"{intensity:.4e}".replace(".", decimal_point), intensity
            else:
                return f"{intensity:.4f}".replace(".", decimal_point), intensity

        def lower_state_energy_str(lower_state_energy: float) -> tuple[str, float]:
            lower_state_energy = from_rec_cm(lower_state_energy)
            if lower_state_energy == 0.0:
                return "0", lower_state_energy
            elif abs(lower_state_energy) < 0.1:
                return f"{lower_state_energy:.4e}".replace(".", decimal_point), lower_state_energy
            else:
                return f"{lower_state_energy:.4f}".replace(".", decimal_point), lower_state_energy

        self.beginResetModel()
        rich_text_in_formulas: bool = self._settings.rich_text_in_formulas
        self._data = list(
            set(
                FoundLinesModel.DataType(
                    species_tag,
                    best_name(entries[species_tag], rich_text_in_formulas),
                    *frequency_str(line[FREQUENCY]),
                    *intensity_str(line[INTENSITY]),
                    *lower_state_energy_str(line[LOWER_STATE_ENERGY]),
                )
                for species_tag in entries
                for line in entries[species_tag][LINES]
            )
        )
        self._rows_loaded = FoundLinesModel.ROW_BATCH_COUNT
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.beginResetModel()
        key = {
            FoundLinesModel.Columns.SubstanceName: (
                lambda line: (line.name, line.frequency, line.intensity, line.lower_state_energy)
            ),
            FoundLinesModel.Columns.Frequency: (
                lambda line: (line.frequency, line.intensity, line.name, line.lower_state_energy)
            ),
            FoundLinesModel.Columns.Intensity: (
                lambda line: (line.intensity, line.frequency, line.name, line.lower_state_energy)
            ),
            FoundLinesModel.Columns.LowerStateEnergy: (
                lambda line: (line.lower_state_energy, line.intensity, line.frequency, line.name)
            ),
        }[FoundLinesModel.Columns(column)]
        self._data.sort(key=key, reverse=bool(order != Qt.SortOrder.AscendingOrder))
        self.endResetModel()

    def canFetchMore(self, index: QModelIndex | QPersistentModelIndex = QModelIndex()) -> bool:
        return len(self._data) > self._rows_loaded

    def fetchMore(self, index: QModelIndex | QPersistentModelIndex = QModelIndex()) -> None:
        # https://sateeshkumarb.wordpress.com/2012/04/01/paginated-display-of-table-data-in-pyqt/
        remainder: int = len(self._data) - self._rows_loaded
        if remainder <= 0:
            return
        items_to_fetch: int = min(remainder, FoundLinesModel.ROW_BATCH_COUNT)
        self.beginInsertRows(index, self._rows_loaded, self._rows_loaded + items_to_fetch - 1)
        self._rows_loaded += items_to_fetch
        self.endInsertRows()
