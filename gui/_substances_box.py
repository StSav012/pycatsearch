# -*- coding: utf-8 -*-
from typing import List, Optional, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QCheckBox, QGroupBox, QLineEdit, QListWidget, \
    QListWidgetItem, QPushButton, QVBoxLayout

from catalog import Catalog
from gui._settings import Settings
from utils import *

__all__ = ['SubstancesBox']


class SubstancesBox(QGroupBox):
    def __init__(self, catalog: Catalog, settings: Settings, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._catalog: Catalog = catalog
        self._settings: Settings = settings
        self._selected_substances: Set[str] = set()

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
        self._list_substance.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._list_substance.setDropIndicatorShown(False)
        self._list_substance.setAlternatingRowColors(True)
        self._list_substance.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._list_substance.setSelectionBehavior(QAbstractItemView.SelectRows)
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

        self.load_settings()

    def update_selected_substances(self):
        if self.isChecked():
            for i in range(self._list_substance.count()):
                item: QListWidgetItem = self._list_substance.item(i)
                if item.checkState() == Qt.Checked:
                    self._selected_substances.add(item.text())
                else:
                    self._selected_substances.discard(item.text())
        else:
            self._selected_substances.clear()

    def filter_substances_list(self, filter_text: str) -> List[str]:
        list_items: List[str] = []
        if filter_text:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if (name_key in entry and plain_text_name.startswith(filter_text)
                            and plain_text_name not in list_items):
                        list_items.append(plain_text_name)
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if name_key in entry and filter_text in plain_text_name and plain_text_name not in list_items:
                        list_items.append(plain_text_name)
            if filter_text.isdecimal():
                for entry in self._catalog.catalog:
                    if SPECIES_TAG in entry and str(entry[SPECIES_TAG]).startswith(filter_text):
                        list_items.append(str(entry[SPECIES_TAG]))
        else:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self._catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if plain_text_name not in list_items:
                        list_items.append(plain_text_name)
            list_items = sorted(list_items)
        return list_items

    def fill_substances_list(self, filter_text: Optional[str] = None):
        if not filter_text:
            filter_text = self._text_substance.text()

        self.update_selected_substances()
        self._list_substance.clear()

        for text in self.filter_substances_list(filter_text):
            new_item: QListWidgetItem = QListWidgetItem(text)
            new_item.setFlags(int(new_item.flags()) | Qt.ItemIsUserCheckable)
            new_item.setCheckState(Qt.Checked if text in self._selected_substances else Qt.Unchecked)
            self._list_substance.addItem(new_item)

    def on_text_changed(self, current_text: str):
        self.fill_substances_list(current_text)

    def on_check_save_selection_toggled(self, new_state):
        if not new_state:
            self._selected_substances.clear()
            self.update_selected_substances()

    def on_button_select_none_clicked(self):
        for i in range(self._list_substance.count()):
            self._list_substance.item(i).setCheckState(Qt.Unchecked)
        self._selected_substances.clear()

    def load_settings(self):
        self._settings.beginGroup('search')
        self._settings.beginGroup('selection')
        self._text_substance.setText(self._settings.value('filter', self._text_substance.text(), str))
        self._check_keep_selection.setChecked(self._settings.value('isPersistent', False, bool))
        self.setChecked(self._settings.value('enabled', self.isChecked(), bool))
        self._settings.endGroup()
        self._settings.endGroup()

    def save_settings(self):
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
    def catalog(self, new_value: Catalog):
        self._catalog = new_value
        self.fill_substances_list()

    @property
    def selected_substances(self) -> Set[str]:
        return self._selected_substances
