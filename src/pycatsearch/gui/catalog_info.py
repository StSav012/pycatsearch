# -*- coding: utf-8 -*-
from __future__ import annotations

import enum
from pathlib import Path
from typing import Iterable, cast

from qtpy.QtCore import QDateTime, QLocale, QModelIndex, QTimeZone, QUrl, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QDesktopServices
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import qta_icon
from .selectable_label import SelectableLabel
from .settings import Settings
from .titled_list_widget import TitledListWidget
from .update_dialog import UpdateDialog
from ..catalog import Catalog, CatalogSourceInfo

__all__ = ["CatalogInfo"]


class SourcesList(QTableWidget):
    catalogUpdated: Signal = Signal(name="catalogUpdated")

    class Columns(enum.IntEnum):
        FileLocation = 0
        BuildTime = 1

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.settings: Settings = settings

        self.setAlternatingRowColors(True)
        self.setColumnCount(len(SourcesList.Columns.__members__))
        self.setCornerButtonEnabled(False)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setHorizontalHeaderLabels([self.tr("Filename"), self.tr("Build Time")])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setHighlightSections(False)

        self._context_menu: QMenu = QMenu(self)
        self._context_menu.setDefaultAction(
            self._context_menu.addAction(
                qta_icon("mdi6.target"), self.tr("Open File &Location"), self._on_open_file_location_triggered
            )
        )
        self._context_menu.addSeparator()
        self._context_menu.addAction(
            qta_icon("mdi6.update"), self.tr("&Update Catalog"), self._on_update_catalog_triggered
        )

        self.cellDoubleClicked.connect(self._on_item_double_clicked)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if not self.selectedIndexes():
            return super().contextMenuEvent(event)
        self._context_menu.exec(event.globalPos())
        return super().contextMenuEvent(event)

    def _selected_row(self) -> int | None:
        if not self.selectedIndexes():
            return None
        return cast(QModelIndex, self.selectedIndexes()[0]).row()

    def _file_location(self, row: int) -> Path | None:
        item: QTableWidgetItem | None = self.item(row, SourcesList.Columns.FileLocation)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _locate_file(self, row: int) -> bool:
        file_location: Path | None = self._file_location(row)
        if file_location is None:
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_location.parent)))

    @Slot(int, int)
    def _on_item_double_clicked(self, row: int, _column: int) -> None:
        self._locate_file(row)

    @Slot()
    def _on_open_file_location_triggered(self) -> None:
        row: int | None = self._selected_row()
        if row is None:
            return
        self._locate_file(row)

    @Slot()
    def _on_update_catalog_triggered(self) -> None:
        row: int | None = self._selected_row()
        if row is None:
            return
        file_location: Path | None = self._file_location(row)
        if file_location is None:
            return
        ud: UpdateDialog = UpdateDialog(
            settings=self.settings,
            existing_catalog_location=file_location,
            parent=self.parent(),
        )
        if ud.exec():
            self.catalogUpdated.emit()

    def extend(self, info: Iterable[CatalogSourceInfo]) -> None:
        row: int
        info_item: CatalogSourceInfo
        item: QTableWidgetItem
        for row, info_item in enumerate(info, start=self.rowCount()):
            self.setRowCount(row + 1)
            item = QTableWidgetItem(str(info_item.filename))
            item.setToolTip(str(info_item.filename))
            item.setData(Qt.ItemDataRole.UserRole, info_item.filename)
            self.setItem(row, SourcesList.Columns.FileLocation, item)
            if info_item.build_datetime is not None:
                qt_datetime: QDateTime = QDateTime(info_item.build_datetime)
                qt_datetime.setTimeZone(QTimeZone(round(info_item.build_datetime.utcoffset().total_seconds())))
                item = QTableWidgetItem(QLocale().toString(qt_datetime))
                self.setItem(row, SourcesList.Columns.BuildTime, item)
        self.setColumnHidden(
            SourcesList.Columns.BuildTime,
            all(self.item(row, SourcesList.Columns.BuildTime) is None for row in range(self.rowCount())),
        )
        self.resizeColumnsToContents()


class CatalogInfo(QDialog):
    """A simple dialog that displays the information about the loaded catalog(s)"""

    catalogUpdated: Signal = Signal(name="catalogUpdated")

    def __init__(self, settings: Settings, catalog: Catalog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(self.tr("Catalog Info"))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QVBoxLayout = QVBoxLayout(self)

        sources_list: SourcesList = SourcesList(settings=settings, parent=self)
        layout.addWidget(sources_list)
        sources_list.extend(catalog.sources_info)
        sources_list.catalogUpdated.connect(self._on_catalog_updated)

        frequency_limits_list: TitledListWidget = TitledListWidget(self)
        frequency_limits_list.setTitle(self.tr("Frequency limits:"))
        layout.addWidget(frequency_limits_list)
        locale: QLocale = QLocale()
        frequency_limits_list.addItems(
            [
                self.tr("{min_frequency} to {max_frequency} MHz").format(
                    min_frequency=locale.toString(min(frequency_limit)),
                    max_frequency=locale.toString(max(frequency_limit)),
                )
                for frequency_limit in catalog.frequency_limits
            ]
        )

        stat_layout: QFormLayout = QFormLayout()
        stat_layout.addRow(self.tr("Total number of substances:"), SelectableLabel(str(catalog.entries_count)))
        layout.addLayout(stat_layout, 0)

        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.adjustSize()

    @Slot()
    def _on_catalog_updated(self) -> None:
        self.reject()
        self.catalogUpdated.emit()
