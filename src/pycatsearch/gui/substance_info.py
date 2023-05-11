# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Collection

from qtpy.QtCore import QModelIndex, Qt, Slot
from qtpy.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout,
                            QWidget)

from .selectable_label import SelectableLabel
from ..catalog import Catalog
from ..utils import *

__all__ = ['SubstanceInfoSelector', 'SubstanceInfo']


class SubstanceInfoSelector(QDialog):
    def __init__(self, catalog: Catalog, entry_ids: Collection[int],
                 allow_html: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._catalog: Catalog = catalog
        self.setModal(True)
        self.setWindowTitle(self.tr('Select Substance'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QVBoxLayout = QVBoxLayout(self)
        self._list_box: QListWidget = QListWidget(self)
        self._list_box.itemSelectionChanged.connect(self._on_list_selection_changed)
        self._list_box.doubleClicked.connect(self._on_list_double_clicked)
        layout.addWidget(self._list_box)
        entry_ids = set(entry_ids)
        for entry in catalog.catalog:
            if not entry_ids:
                break  # nothing to search for
            if entry[ID] in entry_ids:
                entry_ids.discard(entry[ID])  # don't search for the ID again
                # don't specify the parent here: https://t.me/qtforpython/20950
                item: QListWidgetItem = QListWidgetItem()
                item.setData(Qt.ItemDataRole.ToolTipRole, str(entry[SPECIES_TAG]))
                item.setData(Qt.ItemDataRole.UserRole, entry[ID])
                self._list_box.addItem(item)
                self._list_box.setItemWidget(item, QLabel(best_name(entry, allow_html=allow_html)))
        self._buttons: QDialogButtonBox = QDialogButtonBox(
            (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close), self)
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    @Slot()
    def _on_list_selection_changed(self) -> None:
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(self._list_box.selectedIndexes()))

    @Slot(QModelIndex)
    def _on_list_double_clicked(self, index: QModelIndex) -> None:
        self.hide()
        item: QListWidgetItem = self._list_box.item(index.row())
        syn: SubstanceInfo = SubstanceInfo(self._catalog, item.data(Qt.ItemDataRole.UserRole), self.parent())
        syn.exec()
        self.accept()

    @Slot()
    def _on_accept(self) -> None:
        selected_items: list[QListWidgetItem] = self._list_box.selectedItems()
        if not selected_items:
            return
        self.hide()
        item: QListWidgetItem = selected_items.pop()
        syn: SubstanceInfo = SubstanceInfo(self._catalog, item.data(Qt.ItemDataRole.UserRole), self.parent())
        syn.exec()
        self.accept()


class SubstanceInfo(QDialog):
    """ A simple dialog that displays the information about a substance from the loaded catalog """

    def __init__(self, catalog: Catalog, entry_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(self.tr('Substance Info'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QFormLayout = QFormLayout(self)
        label: SelectableLabel
        for entry in catalog.catalog:
            if entry[ID] == entry_id:
                for key in entry:
                    if key == LINES:
                        continue
                    elif key == STATE_HTML:
                        label = SelectableLabel(chem_html(str(entry[key])), self)
                    elif key == INCHI_KEY:
                        label = SelectableLabel(
                            f'<a href="https://pubchem.ncbi.nlm.nih.gov/#query={entry[key]}">{entry[key]}</a>',
                            self)
                        label.setOpenExternalLinks(True)
                    else:
                        label = SelectableLabel(str(entry[key]), self)
                    layout.addRow(self.tr(HUMAN_READABLE[key]), label)
                break
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
