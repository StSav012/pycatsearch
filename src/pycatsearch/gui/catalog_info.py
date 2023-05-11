# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable, Sequence

from qtpy.QtCore import QAbstractTableModel, QDateTime, QModelIndex, QObject, QTimeZone, Qt
from qtpy.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QTableView, QVBoxLayout, QWidget

from .titled_list_widget import TitledListWidget
from ..catalog import Catalog, CatalogSourceInfo

__all__ = ['CatalogInfo']


class DataModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data: list[CatalogSourceInfo] = []
        self._header: list[str] = []

    @property
    def header(self) -> list[str]:
        return self._header[:self.columnCount()]

    @header.setter
    def header(self, new_header: Iterable[str]) -> None:
        self._header = list(new_header)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return 1 if all(info.build_datetime is None for info in self._data) else 2

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return self._data[index.row()].filename
            if index.column() == 1:
                info: CatalogSourceInfo = self._data[index.row()]
                if info.build_datetime is None:
                    return None
                qt_datetime: QDateTime = QDateTime(info.build_datetime)
                qt_datetime.setTimeZone(QTimeZone(round(info.build_datetime.utcoffset().total_seconds())))
                return qt_datetime.toString()
        return None

    def headerData(self, col: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if (orientation == Qt.Orientation.Horizontal
                and role == Qt.ItemDataRole.DisplayRole and 0 <= col < len(self._header)):
            return str(self._header[col])
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: str,
                      role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        if (orientation == Qt.Orientation.Horizontal
                and role == Qt.ItemDataRole.DisplayRole and 0 <= section < len(self._header)):
            self._header[section] = value
            return True
        return False

    def clear(self) -> None:
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.beginResetModel()
        if column == 0:
            self._data.sort(key=lambda i: i.filename)
        elif column == 1:
            self._data.sort(key=lambda i: i.build_datetime)
        self.endResetModel()

    def append(self, info: CatalogSourceInfo) -> None:
        self.beginResetModel()
        self._data.append(info)
        self.endResetModel()

    def extend(self, info: Sequence[CatalogSourceInfo]) -> None:
        self.beginResetModel()
        self._data.extend(info)
        self.endResetModel()


class SourcesList(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self._model: DataModel = DataModel()
        self._model.header = [self.tr('Filename'), self.tr('Build Time')]
        self.setModel(self._model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setDropIndicatorShown(False)
        self.setDragDropOverwriteMode(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setCornerButtonEnabled(False)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setDefaultSectionSize(180)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setHighlightSections(False)

    def append(self, info: CatalogSourceInfo) -> None:
        self._model.append(info)
        self.resizeColumnsToContents()

    def extend(self, info: Sequence[CatalogSourceInfo]) -> None:
        self._model.extend(info)
        self.resizeColumnsToContents()


class CatalogInfo(QDialog):
    """ A simple dialog that displays the information about the loaded catalog(s) """

    def __init__(self, catalog: Catalog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(self.tr('Catalog Info'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QVBoxLayout = QVBoxLayout(self)

        sources_list: SourcesList = SourcesList(self)
        layout.addWidget(sources_list)
        sources_list.extend(catalog.sources_info)

        frequency_limits_list: TitledListWidget = TitledListWidget(self)
        frequency_limits_list.setTitle(self.tr('Frequency limits:'))
        layout.addWidget(frequency_limits_list)
        frequency_limits_list.addItems([
            self.tr('{frequency_limit[0]} to {frequency_limit[1]} MHz').format(frequency_limit=frequency_limit)
            for frequency_limit in catalog.frequency_limits])

        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
