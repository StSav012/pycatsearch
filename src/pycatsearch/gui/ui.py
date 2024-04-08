# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from math import inf
from pathlib import Path
from typing import Any, final

from qtpy.QtCore import QItemSelection, QMimeData, QModelIndex, QPoint, Qt, Slot
from qtpy.QtGui import QClipboard, QCloseEvent, QCursor, QIcon, QPalette, QPixmap, QScreen
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QDoubleSpinBox,
    QFormLayout,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .about_dialog import about
from .catalog_info import CatalogInfo
from .download_dialog import DownloadDialog
from .catalog_file_dialog import CatalogOpenFileDialog, CatalogSaveFileDialog
from .float_spinbox import FloatSpinBox
from .found_lines_model import FoundLinesModel
from .frequency_box import FrequencyBox
from .html_style_delegate import HTMLDelegate
from .menu_bar import MenuBar
from .preferences import Preferences
from .save_catalog_waiting_screen import SaveCatalogWaitingScreen
from .settings import Settings
from .substance_info import SubstanceInfo
from .substances_box import SubstanceBox
from .. import __version__
from ..catalog import Catalog, CatalogType
from ..utils import ReleaseInfo, a_tag, latest_release, p_tag, remove_html, tag, update_with_pip, wrap_in_html

if sys.version_info < (3, 10):
    from ..utils import zip

__all__ = ["UI"]


def copy_to_clipboard(text: str, text_type: Qt.TextFormat | str = Qt.TextFormat.PlainText) -> None:
    clipboard: QClipboard = QApplication.clipboard()
    if not text:
        return
    mime_data: QMimeData = QMimeData()
    if isinstance(text_type, str):
        mime_data.setData(text_type, text.encode())
    elif text_type == Qt.TextFormat.RichText:
        mime_data.setHtml(wrap_in_html(text))
        mime_data.setText(remove_html(text))
    else:
        mime_data.setText(text)
    clipboard.setMimeData(mime_data, QClipboard.Mode.Clipboard)


@final
class UI(QMainWindow):
    def __init__(self, catalog: Catalog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mainWindow")

        self.catalog: Catalog = catalog
        self.settings: Settings = Settings("SavSoft", "CatSearch", self)

        self.open_dialog: CatalogOpenFileDialog = CatalogOpenFileDialog(settings=self.settings, parent=self)
        self.save_dialog: CatalogSaveFileDialog = CatalogSaveFileDialog(settings=self.settings, parent=self)

        self._central_widget: QSplitter = QSplitter(Qt.Orientation.Vertical, self)
        self._central_widget.setObjectName("horizontalSplitter")
        self._top_matter: QSplitter = QSplitter(Qt.Orientation.Horizontal, self._central_widget)
        self._top_matter.setObjectName("verticalSplitter")
        self._right_matter: QWidget = QWidget(self._central_widget)

        self.spin_intensity: FloatSpinBox = FloatSpinBox(self._central_widget)
        self.spin_temperature: QDoubleSpinBox = QDoubleSpinBox(self._central_widget)

        self.box_substance: SubstanceBox = SubstanceBox(self.catalog, self.settings, self._central_widget)
        self.box_frequency: FrequencyBox = FrequencyBox(self.settings, self._central_widget)
        self.button_search: QPushButton = QPushButton(self._central_widget)

        self.results_model: FoundLinesModel = FoundLinesModel(self.settings, self)
        self.results_table: QTableView = QTableView(self._central_widget)

        self.menu_bar: MenuBar = MenuBar(self)

        self.status_bar: QStatusBar = QStatusBar(self)

        def setup_ui() -> None:
            from . import qta_icon  # import locally to avoid a circular import

            def icon_from_data(data: bytes) -> QIcon:
                # https://ru.stackoverflow.com/a/1032610
                palette: QPalette = self.palette()
                pixmap: QPixmap = QPixmap()
                pixmap.loadFromData(
                    data.strip()
                    .replace(b'"background"', b'"' + palette.window().color().name().encode() + b'"')
                    .replace(b'"foreground"', b'"' + palette.text().color().name().encode() + b'"')
                )
                return QIcon(pixmap)

            # language=SVG
            window_icon: bytes = b"""\
            <svg height="64" width="64" version="1.1">
            <path stroke-linejoin="round" d="m6.722 8.432c-9.05 9.648-6.022 27.23 6.048 33.04 6.269 3.614 13.88 \
            3.1 20-0.1664l20 20c2.013 2.013 5.256 2.013 7.27 0l1.259-1.259c2.013-2.013 2.013-5.256 \
            0-7.27l-19.83-19.83c1.094-1.948 1.868-4.095 2.211-6.403 3.06-13.5-9.72-27.22-23.4-25.12-4.74 \
            0.53-9.28 2.72-12.64 6.104-0.321 0.294-0.626 0.597-0.918 0.908zm8.015 6.192c4.978-5.372 14.79-3.878 17.96 \
            2.714 3.655 6.341-0.6611 15.28-7.902 16.36-7.14 1.62-14.4-5.14-13.29-12.38 0.2822-2.51 1.441-4.907 \
            3.231-6.689z" stroke="background" stroke-width="2.4" fill="foreground"/>
            </svg>"""
            self.setWindowIcon(icon_from_data(window_icon))

            if __version__:
                self.setWindowTitle(self.tr("PyCatSearch (version {0})").format(__version__))
            else:
                self.setWindowTitle(self.tr("PyCatSearch"))
            self.setCentralWidget(self._central_widget)

            layout_right: QVBoxLayout = QVBoxLayout()
            layout_options: QFormLayout = QFormLayout()

            self.results_table.setModel(self.results_model)
            self.results_table.setItemDelegateForColumn(0, HTMLDelegate(self.results_table))
            self.results_table.setMouseTracking(True)
            self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.results_table.setDropIndicatorShown(False)
            self.results_table.setDragDropOverwriteMode(False)
            self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.results_table.setCornerButtonEnabled(False)
            self.results_table.setSortingEnabled(True)
            self.results_table.setAlternatingRowColors(True)
            self.results_table.horizontalHeader().setObjectName("resultsTableHorizontalHeader")
            self.results_table.horizontalHeader().setDefaultSectionSize(180)
            self.results_table.horizontalHeader().setHighlightSections(False)
            self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.results_table.horizontalHeader().setSectionsMovable(True)
            self.results_table.verticalHeader().setVisible(False)
            self.results_table.verticalHeader().setHighlightSections(False)

            # substance selection
            self._top_matter.addWidget(self.box_substance)

            # frequency limits
            layout_right.addWidget(self.box_frequency, 1)

            self.spin_intensity.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter
            )
            self.spin_intensity.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.spin_intensity.setDecimals(2)
            self.spin_intensity.setRange(-inf, inf)
            self.spin_intensity.setSingleStep(0.1)
            self.spin_intensity.setValue(-6.54)
            self.spin_intensity.setStatusTip(self.tr("Limit shown spectral lines"))
            layout_options.addRow(self.tr("Minimal Intensity:"), self.spin_intensity)
            self.spin_temperature.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter
            )
            self.spin_temperature.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.spin_temperature.setMaximum(999.99)
            self.spin_temperature.setValue(300.0)
            self.spin_temperature.setStatusTip(self.tr("Temperature to calculate intensity"))
            self.spin_temperature.setSuffix(self.tr(" K"))
            layout_options.addRow(self.tr("Temperature:"), self.spin_temperature)
            layout_right.addLayout(layout_options, 0)

            self.button_search.setText(self.tr("Show"))
            layout_right.addWidget(self.button_search, 0)

            self._right_matter.setLayout(layout_right)
            self._top_matter.addWidget(self._right_matter)
            self._top_matter.setStretchFactor(0, 1)
            self._top_matter.setChildrenCollapsible(False)

            self._central_widget.addWidget(self._top_matter)
            self._central_widget.addWidget(self.results_table)
            self._central_widget.setStretchFactor(1, 1)
            self._central_widget.setChildrenCollapsible(False)

            self.setMenuBar(self.menu_bar)
            self.setStatusBar(self.status_bar)

            self.button_search.setShortcut("Ctrl+Return")

            self.button_search.setIcon(qta_icon("mdi6.magnify"))

            self.adjustSize()

        setup_ui()

        self.temperature: float = 300.0  # [K]
        self.minimal_intensity: float = -inf  # [log10(nm²×MHz)]

        self.button_search.setDisabled(self.catalog.is_empty)

        self.preferences_dialog: Preferences = Preferences(self.settings, self)

        self.preset_table()

        self.load_settings()

        self.results_table.customContextMenuRequested.connect(self._on_table_context_menu_requested)
        self.results_table.selectionModel().selectionChanged.connect(self._on_table_item_selection_changed)
        self.results_table.doubleClicked.connect(self._on_action_substance_info_triggered)
        self.spin_intensity.valueChanged.connect(self._on_spin_intensity_changed)
        self.spin_temperature.valueChanged.connect(self._on_spin_temperature_changed)
        self.button_search.clicked.connect(self._on_search_requested)
        self.box_frequency.frequencyLimitsChanged.connect(self._on_search_requested)
        self.box_substance.selectedSubstancesChanged.connect(self._on_search_requested)
        self.menu_bar.action_load.triggered.connect(self._on_action_load_triggered)
        self.menu_bar.action_reload.triggered.connect(self._on_action_reload_triggered)
        self.menu_bar.action_save_as.triggered.connect(self._on_action_save_as_triggered)
        self.menu_bar.action_download_catalog.triggered.connect(self._on_action_download_catalog_triggered)
        self.menu_bar.action_preferences.triggered.connect(self._on_action_preferences_triggered)
        self.menu_bar.action_quit.triggered.connect(self._on_action_quit_triggered)
        self.menu_bar.action_check_updates.triggered.connect(self._on_action_check_updates_triggered)
        self.menu_bar.action_about_catalogs.triggered.connect(self._on_action_about_catalogs_triggered)
        self.menu_bar.action_about.triggered.connect(self._on_action_about_triggered)
        self.menu_bar.action_about_qt.triggered.connect(self._on_action_about_qt_triggered)
        self.menu_bar.action_copy.triggered.connect(self._on_action_copy_triggered)
        self.menu_bar.action_select_all.triggered.connect(self._on_action_select_all_triggered)
        self.menu_bar.action_copy_current.triggered.connect(self._on_action_copy_current_triggered)
        self.menu_bar.action_copy_name.triggered.connect(self._on_action_copy_name_triggered)
        self.menu_bar.action_copy_frequency.triggered.connect(self._on_action_copy_frequency_triggered)
        self.menu_bar.action_copy_intensity.triggered.connect(self._on_action_copy_intensity_triggered)
        self.menu_bar.action_copy_lower_state_energy.triggered.connect(
            self._on_action_copy_lower_state_energy_triggered
        )
        self.menu_bar.action_show_substance.toggled.connect(self._on_action_show_substance_toggled)
        self.menu_bar.action_show_frequency.toggled.connect(self._on_action_show_frequency_toggled)
        self.menu_bar.action_show_intensity.toggled.connect(self._on_action_show_intensity_toggled)
        self.menu_bar.action_show_lower_state_energy.toggled.connect(self._on_action_show_lower_state_energy_toggled)
        self.menu_bar.action_substance_info.triggered.connect(self._on_action_substance_info_triggered)
        self.menu_bar.action_clear.triggered.connect(self._on_action_clear_triggered)

        if not self.catalog.is_empty:
            self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)

        if self.settings.check_updates:
            _latest_release: ReleaseInfo = latest_release()
            if (
                _latest_release
                and _latest_release.version != self.settings.ignored_version
                and _latest_release.version > __version__
            ):
                res: QMessageBox.StandardButton = QMessageBox.question(
                    self,
                    self.tr("Release Info"),
                    self.tr(
                        "Version {release.version} published {release.pub_date} is available. "
                        "Would you like to get the update? "
                        "The app will try to restart."
                    ).format(release=_latest_release),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Ignore,
                )
                if res == QMessageBox.StandardButton.Yes:
                    update_with_pip()
                elif res == QMessageBox.StandardButton.Ignore:
                    self.settings.ignored_version = _latest_release.version

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def load_catalog(self, *catalog_file_names: Path) -> bool:
        self.setDisabled(True)
        last_cursor: QCursor = self.cursor()
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.repaint()
        self.catalog = Catalog(*catalog_file_names)
        self.box_substance.catalog = self.catalog
        self.setCursor(last_cursor)
        self.setEnabled(True)
        self.button_search.setDisabled(self.catalog.is_empty)
        self.menu_bar.action_save_as.setDisabled(self.catalog.is_empty)
        if not self.catalog.is_empty:
            self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
        return not self.catalog.is_empty

    @Slot(float)
    def _on_spin_temperature_changed(self, arg1: float) -> None:
        self.temperature = self.settings.to_k(arg1)
        self.fill_table()

    @Slot(float)
    def _on_spin_intensity_changed(self, arg1: float) -> None:
        self.minimal_intensity = self.settings.to_log10_sq_nm_mhz(arg1)
        self.fill_table()

    @Slot(QPoint)
    def _on_table_context_menu_requested(self, pos: QPoint) -> None:
        self.menu_bar.menu_edit.popup(self.results_table.viewport().mapToGlobal(pos))

    @Slot(QItemSelection, QItemSelection)
    def _on_table_item_selection_changed(self, _selected: QItemSelection, _deselected: QItemSelection) -> None:
        self.menu_bar.action_copy.setEnabled(bool(self.results_table.selectionModel().selectedRows()))
        self.menu_bar.action_substance_info.setEnabled(bool(self.results_table.selectionModel().selectedRows()))

    @Slot()
    def _on_action_load_triggered(self) -> None:
        self.status_bar.showMessage(self.tr("Select a catalog file to load."))
        new_catalog_filenames: list[str] = self.open_dialog.get_open_filenames()

        if new_catalog_filenames:
            self.status_bar.showMessage(self.tr("Loading…"))
            if self.load_catalog(*new_catalog_filenames):
                self.status_bar.showMessage(self.tr("Catalogs loaded."))
            else:
                self.status_bar.showMessage(self.tr("Failed to load a catalog."))

        else:
            self.status_bar.clearMessage()

    @Slot()
    def _on_action_reload_triggered(self) -> None:
        if self.catalog.sources:
            self.status_bar.showMessage(self.tr("Loading…"))
            if self.load_catalog(*self.catalog.sources):
                self.status_bar.showMessage(self.tr("Catalogs loaded."))
            else:
                self.status_bar.showMessage(self.tr("Failed to load a catalog."))
        else:
            self.status_bar.clearMessage()

    @Slot()
    def _on_action_save_as_triggered(self) -> None:
        catalog: CatalogType = self.catalog.catalog
        frequency_limits: tuple[float, float] = (self.catalog.min_frequency, self.catalog.max_frequency)
        save_filename: Path | None
        while True:
            if not (save_filename := self.save_dialog.get_save_filename()):
                return

            try:
                ws = SaveCatalogWaitingScreen(
                    self,
                    filename=save_filename,
                    catalog=catalog,
                    frequency_limits=frequency_limits,
                )
                ws.exec()
            except OSError as ex:
                QMessageBox.warning(
                    self,
                    self.tr("Unable to save the catalog"),
                    self.tr("Error {exception} occurred while saving {filename}. Try another location.").format(
                        exception=ex,
                        filename=save_filename,
                    ),
                )
            else:
                return

    def stringify_selection_html(self) -> str:
        """
        Convert selected rows to string for copying as rich text
        :return: the rich text representation of the selected table lines
        """
        if not self.results_table.selectionModel().selectedRows():
            return ""

        units: list[str] = [
            "",
            self.settings.frequency_unit_str,
            self.settings.intensity_unit_str,
            self.settings.energy_unit_str,
        ]
        with_units: bool = self.settings.with_units
        csv_separator: str = self.settings.csv_separator
        actions_checked: list[bool] = [_a.isChecked() for _a in self.menu_bar.menu_columns.actions()]

        def format_value(value: Any, unit: str) -> str:
            return (
                self.tr("{value} {unit}", "format value in html").format(value=value, unit=unit)
                if with_units and unit
                else self.tr("{value}", "format value in html").format(value=value)
            )

        columns_order: list[int] = [
            self.results_table.horizontalHeader().logicalIndex(_c)
            for _c, _a in zip(range(self.results_table.horizontalHeader().count()), actions_checked, strict=True)
            if _a
        ]
        text: list[str] = ["<table>"]
        values: list[str]
        index: QModelIndex
        for index in self.results_table.selectionModel().selectedRows():
            row: FoundLinesModel.DataType = self.results_model.row(index.row())
            values = [
                format_value(_v, _u)
                for _u, _v, _a in zip(
                    units,
                    (row.name, row.frequency_str, row.intensity_str, row.lower_state_energy_str),
                    actions_checked,
                    strict=True,
                )
                if _a
            ]
            text.append(
                "<tr><td>" + f"</td>{csv_separator}<td>".join(values[_c] for _c in columns_order) + "</td></tr>"
            )
        text.append("</table>")
        return self.settings.line_end.join(text)

    @Slot()
    def _on_action_download_catalog_triggered(self) -> None:
        downloader: DownloadDialog = DownloadDialog(
            settings=self.settings,
            frequency_limits=(self.catalog.min_frequency, self.catalog.max_frequency),
            parent=self,
        )
        downloader.exec()

    @Slot()
    def _on_action_preferences_triggered(self) -> None:
        if self.preferences_dialog.exec() == Preferences.DialogCode.Accepted:
            self.fill_parameters()
            if self.results_model.rowCount():
                self.preset_table()
                self.fill_table()
            else:
                self.preset_table()

    @Slot()
    def _on_action_quit_triggered(self) -> None:
        self.close()

    @Slot()
    def _on_action_clear_triggered(self) -> None:
        self.results_model.clear()
        self.preset_table()

    def copy_selected_items(self, col: int) -> None:
        if col >= self.results_model.columnCount():
            return

        def html_list(lines: list[str]) -> str:
            return "<ul><li>" + f"</li>{self.settings.line_end}<li>".join(lines) + "</li></ul>"

        text_to_copy: list[str] = []
        index: QModelIndex
        for index in self.results_table.selectionModel().selectedRows(col) or [
            self.results_table.selectionModel().currentIndex()
        ]:
            if index.isValid():
                text_to_copy.append(self.results_model.data(index))
        if not text_to_copy:
            return
        if col == 0:
            copy_to_clipboard(html_list(text_to_copy), Qt.TextFormat.RichText)
        else:
            copy_to_clipboard(self.settings.line_end.join(text_to_copy), Qt.TextFormat.PlainText)

    @Slot()
    def _on_action_copy_current_triggered(self) -> None:
        self.copy_selected_items(self.results_table.selectionModel().currentIndex().column())

    @Slot()
    def _on_action_copy_name_triggered(self) -> None:
        self.copy_selected_items(0)

    @Slot()
    def _on_action_copy_frequency_triggered(self) -> None:
        self.copy_selected_items(1)

    @Slot()
    def _on_action_copy_intensity_triggered(self) -> None:
        self.copy_selected_items(2)

    @Slot()
    def _on_action_copy_lower_state_energy_triggered(self) -> None:
        self.copy_selected_items(3)

    @Slot()
    def _on_action_copy_triggered(self) -> None:
        copy_to_clipboard(self.stringify_selection_html(), Qt.TextFormat.RichText)

    @Slot()
    def _on_action_select_all_triggered(self) -> None:
        self.results_table.selectAll()

    @Slot()
    def _on_action_substance_info_triggered(self) -> None:
        if self.results_table.selectionModel().selectedRows():
            syn: SubstanceInfo = SubstanceInfo(
                self.catalog,
                self.results_model.row(self.results_table.selectionModel().selectedRows()[0].row()).species_tag,
                inchi_key_search_url_template=self.settings.inchi_key_search_url_template,
                parent=self,
            )
            syn.exec()

    def toggle_results_table_column_visibility(self, column: int, is_visible: bool) -> None:
        if is_visible != self.results_table.isColumnHidden(column):
            return
        if is_visible:
            self.results_table.showColumn(column)
        else:
            self.results_table.hideColumn(column)

    @Slot(bool)
    def _on_action_show_substance_toggled(self, is_checked: bool) -> None:
        self.toggle_results_table_column_visibility(0, is_checked)

    @Slot(bool)
    def _on_action_show_frequency_toggled(self, is_checked: bool) -> None:
        self.toggle_results_table_column_visibility(1, is_checked)

    @Slot(bool)
    def _on_action_show_intensity_toggled(self, is_checked: bool) -> None:
        self.toggle_results_table_column_visibility(2, is_checked)

    @Slot(bool)
    def _on_action_show_lower_state_energy_toggled(self, is_checked: bool) -> None:
        self.toggle_results_table_column_visibility(3, is_checked)

    @Slot()
    def _on_action_check_updates_triggered(self) -> None:
        _latest_release: ReleaseInfo = latest_release()
        if not _latest_release:
            QMessageBox.warning(self, self.tr("Release Info"), self.tr("Update check failed."))
        elif _latest_release.version > __version__:
            res: QMessageBox.StandardButton = QMessageBox.question(
                self,
                self.tr("Release Info"),
                self.tr(
                    "Version {release.version} published {release.pub_date} is available. "
                    "Would you like to get the update? "
                    "The app will try to restart."
                ).format(release=_latest_release),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Ignore,
            )
            if res == QMessageBox.StandardButton.Yes:
                update_with_pip()
            elif res == QMessageBox.StandardButton.Ignore:
                self.settings.ignored_version = _latest_release.version
        else:
            QMessageBox.information(self, self.tr("Release Info"), self.tr("You are using the latest version."))

    @Slot()
    def _on_action_about_catalogs_triggered(self) -> None:
        if self.catalog:
            ci: CatalogInfo = CatalogInfo(settings=self.settings, catalog=self.catalog, parent=self)
            ci.catalogUpdated.connect(self._on_action_reload_triggered)
            ci.exec()
        else:
            QMessageBox.information(self, self.tr("Catalog Info"), self.tr("No catalogs loaded"))

    @Slot()
    def _on_action_about_triggered(self) -> None:
        lines: list[str] = [
            self.tr(
                "CatSearch is a means of searching through spectroscopy lines catalogs. It's an offline application."
            ),
            self.tr("It relies on the data stored in JSON files."),
            self.tr(
                "One can use their own catalogs as well as download data from "
                '<a href="https://spec.jpl.nasa.gov/">JPL</a> and '
                '<a href="https://cdms.astro.uni-koeln.de/">CDMS</a> spectroscopy databases '
                "available on the Internet."
            ),
            self.tr("Both plain text JSON and GZip/BZip2/LZMA-compressed JSON are supported."),
            self.tr("See {readme_link} for more info.").format(
                readme_link=a_tag(
                    url="https://github.com/StSav012/pycatsearch/blob/master/README.md", text=self.tr("readme")
                )
            ),
            self.tr("CatSearch is licensed under the {license_link}.").format(
                license_link=a_tag(url="https://www.gnu.org/copyleft/lesser.html", text=self.tr("GNU LGPL version 3"))
            ),
            self.tr("The source code is available on {repo_link}.").format(
                repo_link=a_tag(url="https://github.com/StSav012/pycatsearch", text="GitHub")
            ),
        ]
        about(
            self,
            self.tr("About CatSearch"),
            tag("html", "".join(map(p_tag, lines))),
        )

    @Slot()
    def _on_action_about_qt_triggered(self) -> None:
        QMessageBox.aboutQt(self)

    def load_settings(self) -> None:
        with self.settings.section("search"):
            self.temperature = self.settings.value("temperature", self.spin_temperature.value(), float)
            self.minimal_intensity = self.settings.value("intensity", self.spin_intensity.value(), float)

        with self.settings.section("displayedColumns"):
            for column, (key, action) in enumerate(
                zip(
                    ["substance", "frequency", "intensity", "lowerStateEnergy"],
                    [
                        self.menu_bar.action_show_substance,
                        self.menu_bar.action_show_frequency,
                        self.menu_bar.action_show_intensity,
                        self.menu_bar.action_show_lower_state_energy,
                    ],
                    strict=True,
                )
            ):
                is_visible: bool = self.settings.value(key, True, bool)
                action.setChecked(is_visible)
                self.toggle_results_table_column_visibility(column, is_visible)

        # Fallback: Center the window
        screen: QScreen = QApplication.primaryScreen()
        self.move(
            round(0.5 * (screen.size().width() - self.size().width())),
            round(0.5 * (screen.size().height() - self.size().height())),
        )

        self.settings.restore(self)
        self.settings.restore(self._top_matter)
        self.settings.restore(self._central_widget)
        self.settings.restore(self.results_table.horizontalHeader())
        self.fill_parameters()

        if self.settings.load_last_catalogs:
            self.load_catalog(*self.settings.catalog_file_names)

    def save_settings(self) -> None:
        self.settings.catalog_file_names = self.catalog.sources
        with self.settings.section("search"):
            self.settings.setValue("temperature", self.temperature)
            self.settings.setValue("intensity", self.minimal_intensity)

        with self.settings.section("displayedColumns"):
            self.settings.setValue("substance", self.menu_bar.action_show_substance.isChecked())
            self.settings.setValue("frequency", self.menu_bar.action_show_frequency.isChecked())
            self.settings.setValue("intensity", self.menu_bar.action_show_intensity.isChecked())
            self.settings.setValue("lowerStateEnergy", self.menu_bar.action_show_lower_state_energy.isChecked())

        self.settings.save(self)
        self.settings.save(self._top_matter)
        self.settings.save(self._central_widget)
        self.settings.save(self.results_table.horizontalHeader())

        self.box_substance.save_settings()
        self.box_frequency.save_settings()
        self.settings.sync()

    def preset_table(self) -> None:
        self.results_table.clearSelection()
        self.menu_bar.action_copy.setDisabled(True)
        self.menu_bar.action_substance_info.setDisabled(True)
        self.menu_bar.action_select_all.setDisabled(True)
        self.menu_bar.action_clear.setDisabled(True)
        self.menu_bar.menu_copy_only.setDisabled(True)
        self.results_model.update_units()
        self.update()

    def fill_parameters(self) -> None:
        # frequency
        if not self.catalog.is_empty:
            self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
        self.box_frequency.fill_parameters()

        # intensity
        self.spin_intensity.setSuffix(" " + self.settings.intensity_unit_str)
        self.spin_intensity.setValue(self.settings.from_log10_sq_nm_mhz(self.minimal_intensity))

        # temperature
        temperature_suffix: int = self.settings.temperature_unit
        self.spin_temperature.setSuffix(" " + self.settings.TEMPERATURE_UNITS[temperature_suffix])
        if temperature_suffix == 0:  # K
            self.spin_temperature.setValue(self.temperature)
            self.spin_temperature.setMinimum(0.0)
        elif temperature_suffix == 1:  # °C
            self.spin_temperature.setMinimum(-273.15)
            self.spin_temperature.setValue(self.settings.from_k(self.temperature))
        else:
            raise IndexError("Wrong temperature unit index", temperature_suffix)

    def fill_table(self) -> None:
        self.preset_table()

        if self.box_substance.isChecked() and not self.box_substance.selected_substances:
            self.results_model.clear()
            return

        self.results_table.setSortingEnabled(False)

        entries: CatalogType = self.catalog.filter_by_species_tags(
            species_tags=self.box_substance.selected_substances if self.box_substance.isChecked() else None,
            min_frequency=self.box_frequency.min_frequency,
            max_frequency=self.box_frequency.max_frequency,
            min_intensity=self.minimal_intensity,
            temperature=self.temperature,
        )
        self.results_model.set_entries(entries)

        self.results_table.setSortingEnabled(True)
        self.menu_bar.action_select_all.setEnabled(bool(entries))
        self.menu_bar.action_clear.setEnabled(bool(entries))
        self.menu_bar.menu_copy_only.setEnabled(bool(entries))

    @Slot()
    def _on_search_requested(self) -> None:
        self.status_bar.showMessage(self.tr("Searching…"))
        self.setDisabled(True)
        last_cursor: QCursor = self.cursor()
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.repaint()
        self.fill_table()
        self.setCursor(last_cursor)
        self.setEnabled(True)
        self.status_bar.showMessage(self.tr("Ready."))
