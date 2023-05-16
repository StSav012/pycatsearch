# -*- coding: utf-8 -*-
from __future__ import annotations

from qtpy.QtCore import QModelIndex, Qt
from qtpy.QtWidgets import (QAbstractItemView, QCheckBox, QGroupBox, QLineEdit, QListWidget,
                            QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from .settings import Settings
from .substance_info import SubstanceInfo, SubstanceInfoSelector
from ..catalog import Catalog
from ..utils import *

__all__ = ['SubstancesBox']


class SubstancesBox(QGroupBox):
    def __init__(self, catalog: Catalog, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._catalog: Catalog = catalog
        self._settings: Settings = settings
        self._selected_substances: set[str] = set()

        self._layout_substance: QVBoxLayout = QVBoxLayout(self)
        self._text_substance: QLineEdit = QLineEdit(self)
        self._list_substance: QListWidget = QListWidget(self)
        self._check_keep_selection: QCheckBox = QCheckBox(self)
        self._button_select_none: QPushButton = QPushButton(self)

        self.setCheckable(True)
        self.setTitle(self.tr('Search Only For…'))
        self._text_substance.setClearButtonEnabled(True)
        self._text_substance.setPlaceholderText(self._text_substance.tr('Filter'))
        self._layout_substance.addWidget(self._text_substance)
        self._list_substance.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list_substance.setDropIndicatorShown(False)
        self._list_substance.setAlternatingRowColors(True)
        self._list_substance.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list_substance.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list_substance.setSortingEnabled(False)
        self._layout_substance.addWidget(self._list_substance)
        self._check_keep_selection.setStatusTip(
            self._check_keep_selection.tr('Keep substances list selection through filter changes'))
        self._check_keep_selection.setText(self._check_keep_selection.tr('Persistent Selection'))
        self._layout_substance.addWidget(self._check_keep_selection)
        self._button_select_none.setStatusTip(self._button_select_none.tr('Clear substances list selection'))
        self._button_select_none.setText(self._button_select_none.tr('Select None'))
        self._layout_substance.addWidget(self._button_select_none)

        self._text_substance.textChanged.connect(self.on_text_changed)
        self._check_keep_selection.toggled.connect(self.on_check_save_selection_toggled)
        self._button_select_none.clicked.connect(self.on_button_select_none_clicked)
        self._list_substance.doubleClicked.connect(self.on_list_substance_double_clicked)

        self.load_settings()

    def update_selected_substances(self) -> None:
        if self.isChecked():
            for i in range(self._list_substance.count()):
                item: QListWidgetItem = self._list_substance.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    self._selected_substances.add(item.text())
                else:
                    self._selected_substances.discard(item.text())
        else:
            self._selected_substances.clear()

    def filter_substances_list(self, filter_text: str) -> dict[str, set[int]]:
        list_items: dict[str, set[int]] = dict()
        plain_text_name: str
        if filter_text:
            filter_text_lowercase: str = filter_text.casefold()
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name = remove_html(str(entry[name_key]))
                    if (name_key in entry
                            and (plain_text_name.startswith(filter_text)
                                 or (name_key in (NAME, TRIVIAL_NAME)
                                     and plain_text_name.casefold().startswith(filter_text_lowercase)))):
                        if plain_text_name not in list_items:
                            list_items[plain_text_name] = set()
                        list_items[plain_text_name].add(entry[ID])
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name = remove_html(str(entry[name_key]))
                    if (name_key in entry
                            and (filter_text in plain_text_name
                                 or (name_key in (NAME, TRIVIAL_NAME)
                                     and filter_text_lowercase in plain_text_name.casefold()))):
                        if plain_text_name not in list_items:
                            list_items[plain_text_name] = set()
                        list_items[plain_text_name].add(entry[ID])
            if filter_text.isdecimal():
                for entry in self._catalog.catalog:
                    plain_text_name = str(entry[SPECIES_TAG])
                    if SPECIES_TAG in entry and plain_text_name.startswith(filter_text):
                        if plain_text_name not in list_items:
                            list_items[plain_text_name] = set()
                        list_items[plain_text_name].add(entry[ID])
        else:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name = remove_html(str(entry[name_key]))
                    if plain_text_name not in list_items:
                        list_items[plain_text_name] = set()
                    list_items[plain_text_name].add(entry[ID])
            list_items = dict(sorted(list_items.items()))
        return list_items

    def fill_substances_list(self, filter_text: str | None = None) -> None:
        if not filter_text:
            filter_text = self._text_substance.text()

        self.update_selected_substances()
        self._list_substance.clear()

        text: str
        ids: set[int]
        for text, ids in self.filter_substances_list(filter_text).items():
            new_item: QListWidgetItem = QListWidgetItem(text)
            new_item.setData(Qt.ItemDataRole.UserRole, ids)
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            new_item.setCheckState(Qt.CheckState.Checked
                                   if text in self._selected_substances
                                   else Qt.CheckState.Unchecked)
            self._list_substance.addItem(new_item)

    def on_text_changed(self, current_text: str) -> None:
        self.fill_substances_list(current_text)

    def on_check_save_selection_toggled(self, new_state: bool) -> None:
        if not new_state:
            self._selected_substances.clear()
            self.update_selected_substances()

    def on_button_select_none_clicked(self) -> None:
        for i in range(self._list_substance.count()):
            self._list_substance.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._selected_substances.clear()

    def on_list_substance_double_clicked(self, index: QModelIndex) -> None:
        item: QListWidgetItem = self._list_substance.item(index.row())
        ids: set[int] = item.data(Qt.ItemDataRole.UserRole)
        if len(ids) > 1:
            sis: SubstanceInfoSelector = SubstanceInfoSelector(self.catalog, ids, parent=self)
            sis.exec()
        elif ids:  # if not empty
            syn: SubstanceInfo = SubstanceInfo(self.catalog, ids.pop(), parent=self)
            syn.exec()

    def load_settings(self) -> None:
        self._settings.beginGroup('search')
        self._settings.beginGroup('selection')
        self._text_substance.setText(self._settings.value('filter', self._text_substance.text(), str))
        self._check_keep_selection.setChecked(self._settings.value('isPersistent', False, bool))
        self.setChecked(self._settings.value('enabled', self.isChecked(), bool))
        self._settings.endGroup()
        self._settings.endGroup()

    def save_settings(self) -> None:
        self._settings.beginGroup('search')
        self._settings.beginGroup('selection')
        self._settings.setValue('filter', self._text_substance.text())
        self._settings.setValue('isPersistent', self._check_keep_selection.isChecked())
        self._settings.setValue('enabled', self.isChecked())
        self._settings.endGroup()
        self._settings.endGroup()

    @property
    def catalog(self) -> Catalog:
        return self._catalog

    @catalog.setter
    def catalog(self, new_value: Catalog) -> None:
        self._catalog = new_value
        self.fill_substances_list()

    @property
    def selected_substances(self) -> set[str]:
        return self._selected_substances
