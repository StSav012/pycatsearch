# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

from qtpy.QtCore import QDateTime, QLocale, QTimeZone
from qtpy.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QHeaderView, QTableWidget,
                            QTableWidgetItem, QVBoxLayout, QWidget)

from .selectable_label import SelectableLabel
from .titled_list_widget import TitledListWidget
from ..catalog import Catalog, CatalogSourceInfo

__all__ = ['CatalogInfo']


class SourcesList(QTableWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setColumnCount(2)
        self.setCornerButtonEnabled(False)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setHorizontalHeaderLabels([self.tr('Filename'), self.tr('Build Time')])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, self.horizontalHeader().count()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setHighlightSections(False)

    def extend(self, info: Iterable[CatalogSourceInfo]) -> None:
        row: int
        info_item: CatalogSourceInfo
        item: QTableWidgetItem
        for row, info_item in enumerate(info, start=self.rowCount()):
            self.setRowCount(row + 1)
            item = QTableWidgetItem(info_item.filename)
            item.setToolTip(info_item.filename)
            self.setItem(row, 0, item)
            if info_item.build_datetime is not None:
                qt_datetime: QDateTime = QDateTime(info_item.build_datetime)
                qt_datetime.setTimeZone(QTimeZone(round(info_item.build_datetime.utcoffset().total_seconds())))
                item = QTableWidgetItem(QLocale().toString(qt_datetime))
                self.setItem(row, 1, item)
        self.setColumnHidden(1, all(self.item(row, 1) is None for row in range(self.rowCount())))
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
            self.tr('{min_frequency} to {max_frequency} MHz').format(min_frequency=min(frequency_limit),
                                                                     max_frequency=max(frequency_limit))
            for frequency_limit in catalog.frequency_limits])

        stat_layout: QFormLayout = QFormLayout()
        stat_layout.addRow(self.tr('Total number of substances:'), SelectableLabel(str(catalog.entries_count)))
        layout.addLayout(stat_layout, 0)

        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
