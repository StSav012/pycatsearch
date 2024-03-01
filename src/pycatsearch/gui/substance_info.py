# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import suppress
from typing import Any, Collection, TYPE_CHECKING

from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QIcon
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .html_style_delegate import HTMLDelegate
from .selectable_label import SelectableLabel
from .url_label import URLLabel
from ..catalog import Catalog, CatalogEntryType
from ..utils import HUMAN_READABLE, ID, INCHI_KEY, LINES, STATE_HTML, best_name, chem_html

__all__ = ["SubstanceInfoSelector", "SubstanceInfo"]


class SubstanceInfoSelector(QDialog):
    tagSelectionChanged: Signal = Signal(int, bool, name="tagSelectionChanged")

    def __init__(
        self,
        catalog: Catalog,
        species_tags: Collection[int],
        *,
        selected_species_tags: Collection[int] = (),
        allow_html: bool = True,
        inchi_key_search_url_template: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._catalog: Catalog = catalog
        self._inchi_key_search_url_template: str = inchi_key_search_url_template
        self.setModal(True)
        self.setWindowTitle(self.tr("Select Substance"))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QVBoxLayout = QVBoxLayout(self)
        self._list_box: QListWidget = QListWidget(self)
        self._list_box.itemChanged.connect(self._on_list_item_changed)
        self._list_box.doubleClicked.connect(self._on_list_double_clicked)
        self._list_box.setItemDelegateForColumn(0, HTMLDelegate(self._list_box))
        layout.addWidget(self._list_box)
        species_tags = set(species_tags)
        while species_tags:
            species_tag: int = species_tags.pop()
            # don't specify the parent here: https://t.me/qtforpython/20950
            item: QListWidgetItem = QListWidgetItem(best_name(catalog.catalog[species_tag], allow_html=allow_html))
            item.setData(Qt.ItemDataRole.ToolTipRole, str(species_tag))
            item.setData(Qt.ItemDataRole.UserRole, species_tag)
            item.setCheckState(
                Qt.CheckState.Checked if species_tag in selected_species_tags else Qt.CheckState.Unchecked
            )
            self._list_box.addItem(item)
        self._buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        context_menu: QMenu = QMenu(self)
        context_menu.addAction(
            self._icon(
                "dialog-information",
                "mdi6.flask-empty-outline",
                "mdi6.information-variant",
                options=[{}, {"scale_factor": 0.5}],
            ),
            self.tr("Substance &Info"),
            lambda: self._list_box.doubleClicked.emit(self._list_box.currentIndex()),
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

    @Slot(QListWidgetItem)
    def _on_list_item_changed(self, item: QListWidgetItem) -> None:
        self.tagSelectionChanged.emit(item.data(Qt.ItemDataRole.UserRole), item.checkState() == Qt.CheckState.Checked)

    @Slot(QModelIndex)
    def _on_list_double_clicked(self, index: QModelIndex) -> None:
        item: QListWidgetItem = self._list_box.item(index.row())
        syn: SubstanceInfo = SubstanceInfo(
            self._catalog,
            item.data(Qt.ItemDataRole.UserRole),
            inchi_key_search_url_template=self._inchi_key_search_url_template,
            parent=self,
        )
        syn.exec()


class SubstanceInfo(QDialog):
    """A simple dialog that displays the information about a substance from the loaded catalog"""

    def __init__(
        self,
        catalog: Catalog,
        species_tag: int,
        inchi_key_search_url_template: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(self.tr("Substance Info"))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())
        layout: QFormLayout = QFormLayout(self)
        label: SelectableLabel
        entry: CatalogEntryType = catalog.catalog[species_tag]
        for key in entry:
            if key == LINES:
                continue
            elif key == ID:
                label = URLLabel(
                    url=f"https://cdms.astro.uni-koeln.de/cdms/portal/catalog/{entry[key]}/",
                    text=f"{entry[key]}",
                    parent=self,
                )
                label.setOpenExternalLinks(True)
            elif key == STATE_HTML:
                label = SelectableLabel(chem_html(str(entry[key])), self)
            elif key == INCHI_KEY and inchi_key_search_url_template:
                label = URLLabel(
                    url=inchi_key_search_url_template.format(InChIKey=entry[key]), text=entry[key], parent=self
                )
                label.setOpenExternalLinks(True)
            else:
                label = SelectableLabel(str(entry[key]), self)
            layout.addRow(self.tr(HUMAN_READABLE[key]), label)
        label = SelectableLabel(str(len(entry[LINES])), self)
        layout.addRow(self.tr("Number of spectral lines"), label)
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # add the texts to the translation table but don't run the code at runtime
        if TYPE_CHECKING:
            self.tr("Catalog")
            self.tr("Lines")
            self.tr("Frequency")
            self.tr("Intensity")
            self.tr("ID")
            self.tr("Molecule")
            self.tr("Structural formula")
            self.tr("Stoichiometric formula")
            self.tr("Molecule symbol")
            self.tr("Species tag")
            self.tr("Name")
            self.tr("Trivial name")
            self.tr("Isotopolog")
            self.tr("State (TeX)")
            self.tr("State (HTML)")
            self.tr("InChI key")
            self.tr("Contributor")
            self.tr("Version")
            self.tr("Date of entry")
            self.tr("Degrees of freedom")
            self.tr("Lower state energy")
