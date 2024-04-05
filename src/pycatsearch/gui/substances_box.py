# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from contextlib import suppress
from typing import Any, Callable

from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QIcon
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .html_style_delegate import HTMLDelegate
from .settings import Settings
from .substance_info import SubstanceInfo, SubstanceInfoSelector
from ..catalog import Catalog, CatalogEntryType
from ..utils import (
    INCHI_KEY,
    ISOTOPOLOG,
    NAME,
    STOICHIOMETRIC_FORMULA,
    STRUCTURAL_FORMULA,
    TRIVIAL_NAME,
    best_name,
    remove_html,
)

__all__ = ["SubstanceBox"]


class SubstanceBox(QGroupBox):
    selectedSubstancesChanged: Signal = Signal(name="selectedSubstancesChanged")

    def __init__(self, catalog: Catalog, settings: Settings, parent: QWidget | None = None) -> None:
        from . import qta_icon  # import locally to avoid a circular import

        super().__init__(parent)

        self._catalog: Catalog = catalog
        self._settings: Settings = settings
        self._selected_substances: set[int] = set()

        self._layout_substance: QVBoxLayout = QVBoxLayout(self)
        self._text_substance: QLineEdit = QLineEdit(self)
        self._list_substance: QListWidget = QListWidget(self)
        self._check_keep_selection: QCheckBox = QCheckBox(self)
        self._button_select_none: QPushButton = QPushButton(self)

        self.setCheckable(True)
        self.setTitle(self.tr("Search Only For…"))
        self._text_substance.setClearButtonEnabled(True)
        self._text_substance.setPlaceholderText(self.tr("Filter"))
        self._layout_substance.addWidget(self._text_substance)
        self._list_substance.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list_substance.setDropIndicatorShown(False)
        self._list_substance.setAlternatingRowColors(True)
        self._list_substance.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list_substance.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list_substance.setSortingEnabled(False)
        self._list_substance.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._list_substance.setItemDelegateForColumn(0, HTMLDelegate(self._list_substance))
        self._layout_substance.addWidget(self._list_substance)
        self._check_keep_selection.setStatusTip(self.tr("Keep substances list selection through filter changes"))
        self._check_keep_selection.setText(self.tr("Persistent Selection"))
        self._layout_substance.addWidget(self._check_keep_selection)
        self._button_select_none.setStatusTip(self.tr("Clear substances list selection"))
        self._button_select_none.setText(self.tr("Select None"))
        self._layout_substance.addWidget(self._button_select_none)

        self._button_select_none.setIcon(qta_icon("mdi6.checkbox-blank-off-outline"))

        self._text_substance.textChanged.connect(self._on_text_changed)
        self._check_keep_selection.toggled.connect(self._on_check_save_selection_toggled)
        self._button_select_none.clicked.connect(self._on_button_select_none_clicked)
        self._list_substance.doubleClicked.connect(self._on_list_substance_double_clicked)
        self._list_substance.itemChanged.connect(self._on_list_substance_item_changed)

        self.load_settings()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        species_tags: set[int] = self._list_substance.currentItem().data(Qt.ItemDataRole.UserRole)
        if not species_tags:
            return super().contextMenuEvent(event)

        context_menu: QMenu = QMenu(self)
        context_menu.addAction(
            self._icon(
                "dialog-information",
                "mdi6.flask-empty-outline",
                "mdi6.information-variant",
                options=[{}, {"scale_factor": 0.5}],
            ),
            self.tr("Substance &Info") if len(species_tags) == 1 else self.tr("&Select Substance"),
            lambda: self._list_substance.doubleClicked.emit(self._list_substance.currentIndex()),
        )
        context_menu.exec(event.globalPos())
        return super().contextMenuEvent(event)

    def _icon(
        self,
        theme_name: str,
        *qta_name: str,
        standard_pixmap: QStyle.StandardPixmap | None = None,
        **qta_specs: Any,
    ) -> QIcon:
        if theme_name and QIcon.hasThemeIcon(theme_name):
            return QIcon.fromTheme(theme_name)

        if qta_name:
            with suppress(ImportError, Exception):
                import qtawesome as qta

                return qta.icon(*qta_name, **qta_specs)  # might raise an `Exception` if the icon is not in the font

        if standard_pixmap is not None:
            return self.style().standardIcon(standard_pixmap)

        return QIcon()

    def _filter_substances_list(self, filter_text: str) -> dict[str, set[int]]:
        list_items: dict[str, set[int]] = dict()
        allow_html: bool = self._settings.rich_text_in_formulas
        plain_text_name: str
        species_tag: int
        entry: CatalogEntryType
        if filter_text:
            is_filter_regexp: bool = False
            if filter_text.startswith("/"):
                is_filter_regexp = True
                closing_slash_position: int = filter_text.rfind("/")
                pattern: re.Pattern[str]
                try:
                    if closing_slash_position:
                        flag: re.RegexFlag = re.RegexFlag.NOFLAG
                        for f in filter_text[closing_slash_position + 1 :].casefold():
                            flag |= {"a": re.A, "i": re.I, "m": re.M, "s": re.S}.get(f, re.RegexFlag.NOFLAG)
                        pattern = re.compile(filter_text[1:closing_slash_position], flag)
                    else:
                        pattern = re.compile(filter_text[1:])
                except re.error:
                    is_filter_regexp = False
                else:
                    for match_function in (pattern.fullmatch, pattern.match, pattern.search):
                        for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA, STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                            for species_tag, entry in self._catalog.catalog.items():
                                with suppress(LookupError):
                                    plain_text_name = remove_html(str(entry[name_key]))
                                    if match_function(plain_text_name):
                                        if plain_text_name not in list_items:
                                            list_items[plain_text_name] = set()
                                        list_items[plain_text_name].add(species_tag)
                                        html_name = best_name(entry, allow_html=allow_html)
                                        try:
                                            list_items[html_name].add(species_tag)
                                        except LookupError:
                                            list_items[html_name] = {species_tag}
            if not is_filter_regexp:
                filter_text_lowercase: str = filter_text.casefold()
                cmp_function: Callable[[str, str], bool]
                for cmp_function in (str.startswith, str.__contains__):
                    for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA, STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                        for species_tag, entry in self._catalog.catalog.items():
                            with suppress(LookupError):
                                plain_text_name = remove_html(str(entry[name_key]))
                                if cmp_function(plain_text_name, filter_text) or (
                                    name_key in (NAME, TRIVIAL_NAME)
                                    and cmp_function(plain_text_name.casefold(), filter_text_lowercase)
                                ):
                                    if plain_text_name not in list_items:
                                        list_items[plain_text_name] = set()
                                    list_items[plain_text_name].add(species_tag)
                                    html_name = best_name(entry, allow_html=allow_html)
                                    try:
                                        list_items[html_name].add(species_tag)
                                    except LookupError:
                                        list_items[html_name] = {species_tag}
            # species tag suspected
            if filter_text.isdecimal():
                for species_tag in self._catalog.catalog:
                    plain_text_name = str(species_tag)
                    if plain_text_name.startswith(filter_text):
                        if plain_text_name not in list_items:
                            list_items[plain_text_name] = set()
                        list_items[plain_text_name].add(species_tag)
            # InChI Key match, see https://en.wikipedia.org/wiki/International_Chemical_Identifier#InChIKey
            if (
                len(filter_text) == 27
                and filter_text[14] == "-"
                and filter_text[25] == "-"
                and filter_text.count("-") == 2
            ):
                for species_tag, entry in self._catalog.catalog.items():
                    plain_text_name = str(entry.get(INCHI_KEY, ""))
                    if plain_text_name == filter_text:
                        if plain_text_name not in list_items:
                            list_items[plain_text_name] = set()
                        list_items[plain_text_name].add(species_tag)
        else:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA, STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for species_tag, entry in self._catalog.catalog.items():
                    plain_text_name = remove_html(str(entry[name_key]))
                    if plain_text_name not in list_items:
                        list_items[plain_text_name] = set()
                    list_items[plain_text_name].add(species_tag)
            list_items = dict(sorted(list_items.items()))
        return list_items

    def _fill_substances_list(self, filter_text: str | None = None) -> None:
        if not filter_text:
            filter_text = self._text_substance.text()

        self._list_substance.clear()

        filtered_items: dict[str, set[int]] = self._filter_substances_list(filter_text)
        text: str
        species_tags: set[int]
        check_state: Qt.CheckState
        for check_state in (Qt.CheckState.Checked, Qt.CheckState.PartiallyChecked, Qt.CheckState.Unchecked):
            for text, species_tags in filtered_items.items():
                new_item_check_state: Qt.CheckState
                if species_tags <= self._selected_substances:
                    new_item_check_state = Qt.CheckState.Checked
                elif species_tags & self._selected_substances:
                    new_item_check_state = Qt.CheckState.PartiallyChecked
                else:
                    new_item_check_state = Qt.CheckState.Unchecked
                if check_state != new_item_check_state:
                    continue
                new_item: QListWidgetItem = QListWidgetItem(text)
                new_item.setData(Qt.ItemDataRole.UserRole, species_tags)
                new_item.setCheckState(new_item_check_state)
                self._list_substance.addItem(new_item)

        if not self._check_keep_selection.isChecked():
            newly_selected_substances: set[int] = set().union(
                *(
                    (self._list_substance.item(row).data(Qt.ItemDataRole.UserRole) & self._selected_substances)
                    for row in range(self._list_substance.count())
                )
            )
            if newly_selected_substances != self._selected_substances:
                self._selected_substances = newly_selected_substances
                self.selectedSubstancesChanged.emit()
        self._text_substance.setFocus()

    @Slot(str)
    def _on_text_changed(self, current_text: str) -> None:
        self._fill_substances_list(current_text)

    @Slot(bool)
    def _on_check_save_selection_toggled(self, new_state: bool) -> None:
        if not new_state:
            newly_selected_substances: set[int] = set().union(
                *(
                    (self._list_substance.item(row).data(Qt.ItemDataRole.UserRole) & self._selected_substances)
                    for row in range(self._list_substance.count())
                )
            )
            if newly_selected_substances != self._selected_substances:
                self._selected_substances = newly_selected_substances
                self.selectedSubstancesChanged.emit()

    @Slot()
    def _on_button_select_none_clicked(self) -> None:
        self._list_substance.blockSignals(True)
        for i in range(self._list_substance.count()):
            self._list_substance.item(i).setCheckState(Qt.CheckState.Unchecked)
        self._list_substance.blockSignals(False)
        self._selected_substances.clear()
        self.selectedSubstancesChanged.emit()

    @Slot(QModelIndex)
    def _on_list_substance_double_clicked(self, index: QModelIndex) -> None:
        @Slot(int, bool)
        def on_tag_selection_changed(species_tag: int, selected: bool) -> None:
            if selected:
                self._selected_substances.add(species_tag)
            else:
                self._selected_substances.discard(species_tag)
            for i in range(self._list_substance.count()):
                _item: QListWidgetItem = self._list_substance.item(i)
                _species_tags: set[int] = _item.data(Qt.ItemDataRole.UserRole)
                new_item_check_state: Qt.CheckState
                if _species_tags <= self._selected_substances:
                    new_item_check_state = Qt.CheckState.Checked
                elif _species_tags & self._selected_substances:
                    new_item_check_state = Qt.CheckState.PartiallyChecked
                else:
                    new_item_check_state = Qt.CheckState.Unchecked
                if _item.checkState() != new_item_check_state:
                    self._list_substance.blockSignals(True)
                    _item.setCheckState(new_item_check_state)
                    self._list_substance.blockSignals(False)
                    self.selectedSubstancesChanged.emit()

        item: QListWidgetItem = self._list_substance.item(index.row())
        species_tags: set[int] = item.data(Qt.ItemDataRole.UserRole).copy()
        if len(species_tags) > 1:
            allow_html: bool = self._settings.rich_text_in_formulas
            sis: SubstanceInfoSelector = SubstanceInfoSelector(
                self.catalog,
                species_tags,
                selected_species_tags=self._selected_substances,
                inchi_key_search_url_template=self._settings.inchi_key_search_url_template,
                allow_html=allow_html,
                parent=self,
            )
            sis.tagSelectionChanged.connect(on_tag_selection_changed)
            sis.exec()
        elif species_tags:  # if not empty
            syn: SubstanceInfo = SubstanceInfo(
                self.catalog,
                species_tags.pop(),
                inchi_key_search_url_template=self._settings.inchi_key_search_url_template,
                parent=self,
            )
            syn.exec()

    @Slot(QListWidgetItem)
    def _on_list_substance_item_changed(self, item: QListWidgetItem) -> None:
        species_tags: set[int] = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            if not self._selected_substances.issuperset(species_tags):
                self._selected_substances |= species_tags
                self.selectedSubstancesChanged.emit()
        else:
            if self._selected_substances.intersection(species_tags):
                self._selected_substances -= species_tags
                self.selectedSubstancesChanged.emit()
        self._list_substance.blockSignals(True)
        another_item: QListWidgetItem
        for i in range(self._list_substance.count()):
            another_item = self._list_substance.item(i)
            another_item_species_tags: set[int] = another_item.data(Qt.ItemDataRole.UserRole)
            if another_item_species_tags <= self._selected_substances:
                another_item.setCheckState(Qt.CheckState.Checked)
            elif another_item_species_tags & self._selected_substances:
                another_item.setCheckState(Qt.CheckState.PartiallyChecked)
            else:
                another_item.setCheckState(Qt.CheckState.Unchecked)
        self._list_substance.blockSignals(False)

    def load_settings(self) -> None:
        with self._settings.section("search"), self._settings.section("selection"):
            self._text_substance.setText(self._settings.value("filter", self._text_substance.text(), str))
            self._check_keep_selection.setChecked(self._settings.value("isPersistent", False, bool))
            self.setChecked(self._settings.value("enabled", self.isChecked(), bool))

    def save_settings(self) -> None:
        with self._settings.section("search"), self._settings.section("selection"):
            self._settings.setValue("filter", self._text_substance.text())
            self._settings.setValue("isPersistent", self._check_keep_selection.isChecked())
            self._settings.setValue("enabled", self.isChecked())

    @property
    def catalog(self) -> Catalog:
        return self._catalog

    @catalog.setter
    def catalog(self, new_value: Catalog) -> None:
        self._catalog = new_value
        self._fill_substances_list()

    @property
    def selected_substances(self) -> set[int]:
        if not self.isChecked():
            return set()
        return self._selected_substances
