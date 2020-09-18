# -*- coding: utf-8 -*-
import math
from base64 import b64encode
from typing import Dict, List, Tuple, Type, Union

from PyQt5.QtCore import QAbstractTableModel, QByteArray, QModelIndex, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QAbstractTextDocumentLayout, QCloseEvent, QIcon, QPainter, QPixmap, QTextDocument
from PyQt5.QtWidgets import QAbstractItemView, QAbstractSpinBox, QApplication, QDesktopWidget, \
    QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout, QHeaderView, QMainWindow, QMessageBox, QPushButton, \
    QStatusBar, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTableView, QTableWidgetSelectionRange, QWidget

from catalog import Catalog
from gui._float_spinbox import FloatSpinBox
from gui._frequency_box import FrequencyBox
from gui._menu_bar import MenuBar
from gui._preferences import Preferences
from gui._settings import Settings
from gui._substance_info import SubstanceInfo
from gui._substances_box import SubstancesBox
from utils import *

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()

CatalogEntry: Final[Type] = Dict[str, Union[int, str, List[Dict[str, float]]]]


def copy_to_clipboard(text: str, text_type: Union[Qt.TextFormat, str] = Qt.PlainText):
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtCore import QMimeData

    clipboard: QClipboard = QApplication.clipboard()
    mime_data: QMimeData = QMimeData()
    if isinstance(text_type, str):
        mime_data.setData(text_type, text.encode())
    elif text_type == Qt.RichText:
        mime_data.setHtml(wrap_in_html(text))
        mime_data.setText(remove_html(text))
    else:
        mime_data.setText(text)
    clipboard.setMimeData(mime_data, QClipboard.Clipboard)


class HTMLDelegate(QStyledItemDelegate):
    @staticmethod
    def anchorAt(html, point):
        doc = QTextDocument()
        doc.setHtml(html)
        text_layout = doc.documentLayout()
        return text_layout.anchorAt(point)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        self.initStyleOption(option, index)
        if option.widget:
            style: QStyle = option.widget.style()
        else:
            style: QStyle = QApplication.style()
        doc: QTextDocument = QTextDocument()
        doc.setHtml(option.text)
        option.text = ''
        style.drawControl(QStyle.CE_ItemViewItem, option, painter)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        text_rect: QRect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        painter.translate(0, 0.5 * (option.rect.height() - doc.size().height()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        doc: QTextDocument = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())


class ListStore(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: List[CatalogEntry] = []
        self._data: List[Tuple[int, str, float, float, float]] = []

        unit_format: Final[str] = self.tr('%s [%s]', 'unit format')
        self._header: Final[List[str]] = [
            self.tr('Substance'),
            unit_format % (self.tr("Frequency"), self.parent().settings.frequency_unit_str),
            unit_format % (self.tr("Intensity"), self.parent().settings.intensity_unit_str),
            unit_format % (self.tr("Lower state energy"), self.parent().settings.energy_unit_str),
        ]

    def update_units(self):
        unit_format: Final[str] = self.tr('%s [%s]', 'unit format')
        self._header[1] = unit_format % (self.tr("Frequency"), self.parent().settings.frequency_unit_str)
        self._header[2] = unit_format % (self.tr("Intensity"), self.parent().settings.intensity_unit_str)
        self._header[3] = unit_format % (self.tr("Lower state energy"), self.parent().settings.energy_unit_str)

    def rowCount(self, parent=None) -> int:
        return len(self._entries)

    def columnCount(self, parent=None) -> int:
        return len(self._header)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                data_column: Final[int] = {0: 1, 1: 2, 2: 4, 3: 6}[index.column()]
                return self._data[index.row()][data_column]
        return None

    def row(self, row_index: int) -> Tuple[int, str, float, float, float]:
        return self._data[row_index]

    def item(self, row_index: int, column_index: int) -> Tuple[int, str, float, float, float]:
        data_column: Final[int] = {0: 1, 1: 2, 2: 4, 3: 6}[column_index]
        return self._data[row_index][data_column]

    def raw_item(self, row_index: int, column_index: int) -> Tuple[int, str, float, float, float]:
        return self._data[row_index][column_index]

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[col]
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value, role: int = ...) -> bool:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < len(self._header):
            self._header[section] = value
            return True
        return False

    def clear(self):
        self.set_entries([])

    def set_entries(self, new_data: List[CatalogEntry]):
        def frequency_str(line: Dict[str, float]) -> Tuple[str, float]:
            frequency: float = self.parent().settings.from_mhz(line[FREQUENCY])
            frequency_suffix: int = self.parent().settings.frequency_unit
            precision: int = [4, 7, 8, 8][frequency_suffix]
            return f'{frequency:.{precision}f}', frequency

        def intensity_str(line: Dict[str, float]) -> Tuple[str, float]:
            intensity: float = self.parent().settings.from_log10_sq_nm_mhz(line[INTENSITY])
            if intensity == 0.0:
                return '0', intensity
            elif abs(intensity) < 0.1:
                return f'{intensity:.4e}', intensity
            else:
                return f'{intensity:.4f}', intensity

        def lower_state_energy_str(line: Dict[str, float]) -> Tuple[str, float]:
            lower_state_energy: float = self.parent().settings.from_rec_cm(line[LOWER_STATE_ENERGY])
            if lower_state_energy == 0.0:
                return '0', lower_state_energy
            elif abs(lower_state_energy) < 0.1:
                return f'{lower_state_energy:.4e}', lower_state_energy
            else:
                return f'{lower_state_energy:.4f}', lower_state_energy

        self.beginResetModel()
        self._entries = new_data[:]
        entry: CatalogEntry
        self._data = [
            (
                entry[ID],
                best_name(entry, self.parent().settings.rich_text_in_formulas),
                *frequency_str(line),
                *intensity_str(line),
                *lower_state_energy_str(line),
            )
            for entry in self._entries
            for line in entry[LINES]
        ]
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self.beginResetModel()
        data_column: Final[int] = {0: 1, 1: 3, 2: 5, 3: 7}[column]
        self._data.sort(key=lambda l: l[data_column], reverse=bool(order != Qt.AscendingOrder))
        self.endResetModel()


class UI(QMainWindow):
    def __init__(self, catalog: Catalog, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog: Catalog = catalog
        self.settings: Settings = Settings('SavSoft', 'CatSearch', self)

        self.central_widget: QWidget = QWidget(self)
        self.layout_main: QGridLayout = QGridLayout(self.central_widget)

        self.layout_options: QFormLayout = QFormLayout()
        self.spin_intensity: FloatSpinBox = FloatSpinBox(self.central_widget)
        self.spin_temperature: QDoubleSpinBox = QDoubleSpinBox(self.central_widget)

        self.box_substance: SubstancesBox = SubstancesBox(self.catalog, self.settings, self.central_widget)
        self.box_frequency: FrequencyBox = FrequencyBox(self.settings, self.central_widget)
        self.button_search: QPushButton = QPushButton(self.central_widget)

        self.results_model: ListStore = ListStore(self)
        self.results_table: QTableView = QTableView(self.central_widget)

        self.menu_bar: MenuBar = MenuBar(self)

        self.status_bar = QStatusBar(self)

        def setup_ui():
            # https://ru.stackoverflow.com/a/1032610
            window_icon: QPixmap = QPixmap()
            window_icon.loadFromData(QByteArray.fromBase64(b64encode(b'''\
            <svg height="64" width="64" version="1.1">
            <path stroke-linejoin="round" d="m6.722 8.432c-9.05 9.648-6.022 27.23 6.048 33.04 6.269 3.614 13.88 \
            3.1 20-0.1664l20 20c2.013 2.013 5.256 2.013 7.27 0l1.259-1.259c2.013-2.013 2.013-5.256 \
            0-7.27l-19.83-19.83c1.094-1.948 1.868-4.095 2.211-6.403 3.06-13.5-9.72-27.22-23.4-25.12-4.74 \
            0.53-9.28 2.72-12.64 6.104-0.321 0.294-0.626 0.597-0.918 0.908zm8.015 6.192c4.978-5.372 14.79-3.878 17.96 \
            2.714 3.655 6.341-0.6611 15.28-7.902 16.36-7.14 1.62-14.4-5.14-13.29-12.38 0.2822-2.51 1.441-4.907 \
            3.231-6.689z" stroke="#000" stroke-width="2.4" fill="#fff"/>
            </svg>\
            ''')), 'SVG')
            self.setWindowIcon(QIcon(QPixmap(window_icon)))

            if UPDATED:
                self.setWindowTitle(self.tr('PyQtCatSearch') + self.tr(' (as of {0})').format(UPDATED))
            else:
                self.setWindowTitle(self.tr('PyQtCatSearch'))
            self.setCentralWidget(self.central_widget)
            self.layout_main.setColumnStretch(0, 1)
            self.layout_main.setRowStretch(4, 1)

            self.results_table.setModel(self.results_model)
            self.results_table.setItemDelegateForColumn(0, HTMLDelegate())
            self.results_table.setMouseTracking(True)
            self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.results_table.setDropIndicatorShown(False)
            self.results_table.setDragDropOverwriteMode(False)
            self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.results_table.setCornerButtonEnabled(False)
            self.results_table.setSortingEnabled(True)
            self.results_table.setAlternatingRowColors(True)
            self.results_table.horizontalHeader().setDefaultSectionSize(180)
            self.results_table.horizontalHeader().setHighlightSections(False)
            self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.results_table.verticalHeader().setVisible(False)
            self.results_table.verticalHeader().setHighlightSections(False)
            self.layout_main.addWidget(self.results_table, 4, 0, 1, 3)

            # substance selection
            self.layout_main.addWidget(self.box_substance, 0, 0, 4, 1)

            # frequency limits
            self.layout_main.addWidget(self.box_frequency, 0, 1, 2, 1)

            self.spin_intensity.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_intensity.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_intensity.setDecimals(2)
            self.spin_intensity.setMinimum(-math.inf)
            self.spin_intensity.setMaximum(math.inf)
            self.spin_intensity.setSingleStep(0.1)
            self.spin_intensity.setValue(-6.54)
            self.spin_intensity.setStatusTip(self.spin_intensity.tr('Limit shown spectral lines'))
            self.layout_options.addRow(self.layout_options.tr('Minimal Intensity:'), self.spin_intensity)
            self.spin_temperature.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_temperature.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_temperature.setMaximum(999.99)
            self.spin_temperature.setValue(300.0)
            self.spin_temperature.setStatusTip(self.spin_temperature.tr('Temperature to calculate intensity'))
            self.spin_temperature.setSuffix(self.spin_temperature.tr(' K'))
            self.layout_options.addRow(self.layout_options.tr('Temperature:'), self.spin_temperature)
            self.layout_main.addLayout(self.layout_options, 2, 1, 1, 1)

            self.button_search.setText(self.button_search.tr('Show'))
            self.layout_main.addWidget(self.button_search, 3, 1, 1, 1)

            self.setMenuBar(self.menu_bar)
            self.setStatusBar(self.status_bar)

            self.button_search.setShortcut('Ctrl+Return')

            self.adjustSize()

        setup_ui()

        self.temperature: float = 300.0  # [K]
        self.minimal_intensity: float = -math.inf  # [log10(nm²×MHz)]

        self.button_search.setDisabled(self.catalog.is_empty)

        self.preferences_dialog: Preferences = Preferences(self.settings, self)

        self.results_shown: bool = False

        self.preset_table()

        self.load_settings()

        self.results_table.customContextMenuRequested.connect(self.on_table_context_menu_requested)
        self.results_table.selectionModel().selectionChanged.connect(self.on_table_item_selection_changed)
        self.results_table.doubleClicked.connect(self.on_action_substance_info_triggered)
        self.spin_intensity.valueChanged.connect(self.on_spin_intensity_changed)
        self.spin_temperature.valueChanged.connect(self.on_spin_temperature_changed)
        self.button_search.clicked.connect(self.on_button_search_clicked)
        self.menu_bar.action_load.triggered.connect(self.on_action_load_triggered)
        self.menu_bar.action_quit.triggered.connect(self.on_action_quit_triggered)
        self.menu_bar.action_about.triggered.connect(self.on_action_about_triggered)
        self.menu_bar.action_about_qt.triggered.connect(self.on_action_about_qt_triggered)
        self.menu_bar.action_preferences.triggered.connect(self.on_action_preferences_triggered)
        self.menu_bar.action_copy.triggered.connect(self.on_action_copy_triggered)
        self.menu_bar.action_select_all.triggered.connect(self.on_action_select_all_triggered)
        self.menu_bar.action_reload.triggered.connect(self.on_action_reload_triggered)
        self.menu_bar.action_copy_name.triggered.connect(self.on_action_copy_name_triggered)
        self.menu_bar.action_copy_frequency.triggered.connect(self.on_action_copy_frequency_triggered)
        self.menu_bar.action_copy_intensity.triggered.connect(self.on_action_copy_intensity_triggered)
        self.menu_bar.action_copy_lower_state_energy.triggered.connect(self.on_action_copy_lower_state_energy_triggered)
        self.menu_bar.action_show_frequency.toggled.connect(self.on_action_show_frequency_toggled)
        self.menu_bar.action_show_intensity.toggled.connect(self.on_action_show_intensity_toggled)
        self.menu_bar.action_show_lower_state_energy.toggled.connect(self.on_action_show_lower_state_energy_toggled)
        self.menu_bar.action_substance_info.triggered.connect(self.on_action_substance_info_triggered)
        self.menu_bar.action_clear.triggered.connect(self.on_action_clear_triggered)

        if not self.catalog.is_empty:
            self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def on_spin_temperature_changed(self, arg1: float):
        self.temperature = self.settings.to_k(arg1)
        self.fill_table()

    def on_spin_intensity_changed(self, arg1: float):
        self.minimal_intensity = self.settings.to_log10_sq_nm_mhz(arg1)
        if self.results_shown:
            self.fill_table()

    def on_table_context_menu_requested(self, pos: QPoint):
        self.menu_bar.menu_edit.popup(self.results_table.viewport().mapToGlobal(pos))

    def on_table_item_selection_changed(self):
        self.menu_bar.action_copy.setEnabled(bool(self.results_table.selectionModel().selectedRows()))
        self.menu_bar.action_substance_info.setEnabled(bool(self.results_table.selectionModel().selectedRows()))

    def on_action_load_triggered(self):
        self.status_bar.showMessage(self.tr('Select a catalog file to load.'))
        new_catalog_file_names: List[str]
        new_catalog_file_names, _ = QFileDialog.getOpenFileNames(
            self, self.tr('Load Catalog'),
            self.catalog.sources[0] if self.catalog.sources else '',
            '{0} (*.json.gz);;{1} (*.json);;{2} (*.*)'.format(
                self.tr('Compressed JSON'),
                self.tr('JSON'),
                self.tr('All Files')))
        if new_catalog_file_names:
            self.status_bar.showMessage(self.tr('Loading...'))
            self.catalog = Catalog(*new_catalog_file_names)
            self.box_substance.catalog = self.catalog
            self.button_search.setDisabled(self.catalog.is_empty)
            if not self.catalog.is_empty:
                self.status_bar.showMessage(self.tr('Catalogs loaded.'))
                self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
            else:
                self.status_bar.showMessage(self.tr('Failed to load a catalog.'))

        else:
            self.status_bar.clearMessage()

    def on_action_reload_triggered(self):
        if self.catalog.sources:
            self.status_bar.showMessage(self.tr('Loading...'))
            self.catalog = Catalog(*self.catalog.sources)
            self.box_substance.catalog = self.catalog
            self.button_search.setDisabled(self.catalog.is_empty)
            if not self.catalog.is_empty:
                self.status_bar.showMessage(self.tr('Catalogs loaded.'))
                self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
            else:
                self.status_bar.showMessage(self.tr('Failed to load a catalog.'))
        else:
            self.status_bar.clearMessage()

    def stringify_selection_html(self) -> str:
        """
        Convert selected rows to string for copying as rich text
        :return: the rich text representation of the selected table lines
        """
        text: List[str] = []
        r: QModelIndex
        units: Dict[int, str] = {
            1: self.settings.frequency_unit_str,
            2: self.settings.intensity_unit_str,
            3: self.settings.energy_unit_str,
        }
        for r in self.results_table.selectionModel().selectedRows():
            row: Tuple[int, str, float, float, float] = self.results_model.row(r.row())
            text.append(
                '<tr><td>' +
                f'</td>{self.settings.csv_separator}<td>'.join(
                    [row[1]] +
                    [(row[_c * 2] + ((' ' + units[_c]) if self.settings.with_units and _c in units else ''))
                     for _c, _a in zip(range(1, self.results_model.columnCount()),
                                       self.menu_bar.menu_columns.actions())
                     if _a.isChecked()]
                ) +
                '</td></tr>' + self.settings.line_end
            )
        return '<table>' + self.settings.line_end + ''.join(text) + '</table>'

    def on_action_preferences_triggered(self):
        self.preferences_dialog.exec()
        self.fill_parameters()
        if self.results_model.rowCount():
            self.preset_table()
            self.fill_table()
        else:
            self.preset_table()

    def on_action_quit_triggered(self):
        self.close()

    def on_action_clear_triggered(self):
        self.results_model.clear()
        self.preset_table()

    def copy_selected_items(self, col: int):
        if col >= self.results_model.columnCount():
            return

        def html_list(lines: List[str]) -> str:
            return '<ul><li>' + f'</li>{self.settings.line_end}<li>'.join(lines) + '</li></ul>'

        text_to_copy: List[str] = []
        selection: QTableWidgetSelectionRange
        for row in self.results_table.selectionModel().selectedRows(col):
            text_to_copy.append(self.results_model.data(row))
        if col == 0:
            copy_to_clipboard(html_list(text_to_copy), Qt.RichText)
        else:
            copy_to_clipboard(self.settings.line_end.join(text_to_copy), Qt.PlainText)

    def on_action_copy_name_triggered(self):
        self.copy_selected_items(0)

    def on_action_copy_frequency_triggered(self):
        self.copy_selected_items(1)

    def on_action_copy_intensity_triggered(self):
        self.copy_selected_items(2)

    def on_action_copy_lower_state_energy_triggered(self):
        self.copy_selected_items(3)

    def on_action_copy_triggered(self):
        copy_to_clipboard(self.stringify_selection_html(), Qt.RichText)

    def on_action_select_all_triggered(self):
        self.results_table.selectAll()

    def on_action_substance_info_triggered(self):
        if self.results_table.selectionModel().selectedRows():
            syn: SubstanceInfo = SubstanceInfo(
                self.catalog,
                self.results_model.row(self.results_table.selectionModel().selectedRows()[0].row())[0],
                self)
            syn.exec()

    def toggle_results_table_column_visibility(self, column: int, is_visible: bool):
        if is_visible:
            self.results_table.showColumn(column)
        else:
            self.results_table.hideColumn(column)

    def on_action_show_frequency_toggled(self, is_checked: bool):
        self.toggle_results_table_column_visibility(1, is_checked)

    def on_action_show_intensity_toggled(self, is_checked: bool):
        self.toggle_results_table_column_visibility(2, is_checked)

    def on_action_show_lower_state_energy_toggled(self, is_checked: bool):
        self.toggle_results_table_column_visibility(3, is_checked)

    def on_action_about_triggered(self):
        QMessageBox.about(self,
                          self.tr("About CatSearch"),
                          "<html><p>"
                          + self.tr("CatSearch is a means of searching through spectroscopy lines catalogs. "
                                    "It's an offline application.")
                          + "</p><p>"
                          + self.tr("It relies on the data stored in JSON files.")
                          + "</p><p>"
                          + self.tr("One can write his own catalogs as well as convert data from "
                                    "<a href='https://spec.jpl.nasa.gov/'>JPL</a> and "
                                    "<a href='https://astro.uni-koeln.de/'>CDMS</a> spectroscopy databases "
                                    "freely available in the Internet or other sources.")
                          + "</p><p>"
                          + self.tr("Both plain text JSON and GZip compressed JSON are supported.")
                          + "</p><p>"
                          + self.tr('See {0} for more info.')
                          .format('<a href="https://github.com/StSav012/pycatsearch/blob/master/README.md">{0}</a>')
                          .format(self.tr('readme'))
                          + "</p><br><p>"
                          + self.tr("CatSearch is licensed under the {0}.")
                          .format("<a href='https://www.gnu.org/copyleft/lesser.html'>{0}</a>"
                                  .format(self.tr("GNU LGPL version 3")))
                          + "</p><p>"
                          + self.tr("The source code is available on {0}.").format(
                              "<a href='https://github.com/StSav012/pycatsearch'>GitHub</a>")
                          + "</p></html>")

    def on_action_about_qt_triggered(self):
        QMessageBox.aboutQt(self)

    def load_settings(self):
        self.settings.beginGroup('search')
        catalog_file_names: List[str] = []
        for i in range(self.settings.beginReadArray('catalogFiles')):
            self.settings.setArrayIndex(i)
            path: str = self.settings.value('path', '', str)
            if path:
                catalog_file_names.append(path)
        self.settings.endArray()
        if not catalog_file_names:
            catalog_file_names = ['catalog.json.gz', 'catalog.json']
        self.temperature = self.settings.value('temperature', self.spin_temperature.value(), float)
        self.minimal_intensity = self.settings.value('intensity', self.spin_intensity.value(), float)
        self.settings.endGroup()
        self.settings.beginGroup('displayedColumns')
        self.menu_bar.action_show_frequency.setChecked(self.settings.value('frequency', True, bool))
        self.toggle_results_table_column_visibility(1, self.menu_bar.action_show_frequency.isChecked())
        self.menu_bar.action_show_intensity.setChecked(self.settings.value('intensity', True, bool))
        self.toggle_results_table_column_visibility(2, self.menu_bar.action_show_intensity.isChecked())
        self.menu_bar.action_show_lower_state_energy.setChecked(self.settings.value('lowerStateEnergy', False, bool))
        self.toggle_results_table_column_visibility(3, self.menu_bar.action_show_lower_state_energy.isChecked())
        self.settings.endGroup()
        self.settings.beginGroup('window')
        desktop: QDesktopWidget = QApplication.desktop()
        self.move(round(0.5 * (desktop.width() - self.size().width())),
                  round(0.5 * (desktop.height() - self.size().height())))  # Fallback: Center the window
        window_settings = self.settings.value('geometry')
        if window_settings is not None:
            self.restoreGeometry(window_settings)
        window_settings = self.settings.value('state')
        if window_settings is not None:
            self.restoreState(window_settings)
        self.settings.endGroup()
        self.fill_parameters()

        if self.settings.load_last_catalogs:
            self.catalog = Catalog(*catalog_file_names)
            self.button_search.setEnabled(not self.catalog.is_empty)
            if not self.catalog.is_empty:
                self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
                self.box_substance.catalog = self.catalog

    def save_settings(self):
        self.settings.beginGroup('search')
        self.settings.beginWriteArray('catalogFiles', len(self.catalog.sources))
        for i, s in enumerate(self.catalog.sources):
            self.settings.setArrayIndex(i)
            self.settings.setValue('path', s)
        self.settings.endArray()
        self.settings.setValue('temperature', self.temperature)
        self.settings.setValue('intensity', self.minimal_intensity)
        self.settings.endGroup()
        self.settings.beginGroup('displayedColumns')
        self.settings.setValue('frequency', self.menu_bar.action_show_frequency.isChecked())
        self.settings.setValue('intensity', self.menu_bar.action_show_intensity.isChecked())
        self.settings.setValue('lowerStateEnergy', self.menu_bar.action_show_lower_state_energy.isChecked())
        self.settings.endGroup()
        self.settings.beginGroup('window')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('state', self.saveState())
        self.settings.endGroup()
        self.box_substance.save_settings()
        self.box_frequency.save_settings()
        self.settings.sync()

    def preset_table(self):
        self.results_shown = False
        self.results_table.clearSelection()
        self.menu_bar.action_copy.setDisabled(True)
        self.menu_bar.action_substance_info.setDisabled(True)
        self.menu_bar.action_select_all.setDisabled(True)
        self.menu_bar.action_clear.setDisabled(True)
        self.menu_bar.menu_copy_only.setDisabled(True)
        self.results_model.update_units()
        self.update()

    def fill_parameters(self):
        # frequency
        if not self.catalog.is_empty:
            self.box_frequency.set_frequency_limits(self.catalog.min_frequency, self.catalog.max_frequency)
        self.box_frequency.fill_parameters()

        # intensity
        self.spin_intensity.setSuffix(' ' + self.settings.intensity_unit_str)
        self.spin_intensity.setValue(self.settings.from_log10_sq_nm_mhz(self.minimal_intensity))

        # temperature
        temperature_suffix: int = self.settings.temperature_unit
        self.spin_temperature.setSuffix(' ' + self.settings.TEMPERATURE_UNITS[temperature_suffix])
        if temperature_suffix == 0:  # K
            self.spin_temperature.setValue(self.temperature)
            self.spin_temperature.setMinimum(0.0)
        elif temperature_suffix == 1:  # °C
            self.spin_temperature.setMinimum(-273.15)
            self.spin_temperature.setValue(self.settings.from_k(self.temperature))
        else:
            raise IndexError('Wrong temperature unit index', temperature_suffix)

    def fill_table(self):
        self.preset_table()
        self.results_table.setSortingEnabled(False)

        entries: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = \
            (sum(
                (
                    self.catalog.filter(min_frequency=self.box_frequency.min_frequency,
                                        max_frequency=self.box_frequency.max_frequency,
                                        min_intensity=self.minimal_intensity,
                                        any_name_or_formula=name,
                                        temperature=self.temperature,
                                        timeout=self.settings.timeout)
                    for name in self.box_substance.selected_substances
                ),
                []
            ) if self.box_substance.selected_substances and self.box_substance.isChecked()
             else self.catalog.filter(min_frequency=self.box_frequency.min_frequency,
                                      max_frequency=self.box_frequency.max_frequency,
                                      min_intensity=self.minimal_intensity,
                                      temperature=self.temperature,
                                      timeout=self.settings.timeout))
        self.results_model.set_entries(entries)

        self.results_table.setSortingEnabled(True)
        self.menu_bar.action_select_all.setEnabled(bool(entries))
        self.menu_bar.action_clear.setEnabled(bool(entries))
        self.menu_bar.menu_copy_only.setEnabled(bool(entries))
        self.results_shown = True

    def on_button_search_clicked(self):
        self.status_bar.showMessage(self.tr('Searching...'))
        self.box_substance.update_selected_substances()
        self.fill_table()
        self.status_bar.showMessage(self.tr('Ready.'))
