# -*- coding: utf-8 -*-
import math
import sys
from base64 import b64encode
from typing import Dict, List, Optional, Set, Type, Union

from PyQt5.QtCore import QByteArray, QPoint, Qt
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap, QPalette
from PyQt5.QtWidgets import QAbstractItemView, QAbstractSpinBox, QAction, QApplication, QCheckBox, QDesktopWidget, \
    QDoubleSpinBox, QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHeaderView, QLabel, QLineEdit, QListWidget, \
    QListWidgetItem, QMainWindow, QMenu, QMenuBar, QMessageBox, QPushButton, QStatusBar, QStyle, QTabWidget, \
    QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange, QWidget

from catalog import Catalog
from gui.floatspinbox import FloatSpinBox
from gui.preferences import Preferences
from gui.settings import Settings
from gui.substance_info import SubstanceInfo
from utils import *

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()


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


class UI(QMainWindow):
    MAX_ENTRIES_COUNT: Final[int] = 64

    def __init__(self, catalog: Catalog, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.central_widget: QWidget = QWidget(self)
        self.layout_main: QGridLayout = QGridLayout(self.central_widget)
        self.results_table: QTableWidget = QTableWidget(self.central_widget)
        self.box_substance: QGroupBox = QGroupBox(self.central_widget)
        self.layout_substance: QGridLayout = QGridLayout(self.box_substance)
        self.text_substance: QLineEdit = QLineEdit(self.box_substance)
        self.list_substance: QListWidget = QListWidget(self.box_substance)
        self.check_keep_selection: QCheckBox = QCheckBox(self.box_substance)
        self.button_select_none: QPushButton = QPushButton(self.box_substance)
        self.layout_options: QFormLayout = QFormLayout()
        self.spin_intensity: FloatSpinBox = FloatSpinBox(self.central_widget)
        self.spin_temperature: QDoubleSpinBox = QDoubleSpinBox(self.central_widget)
        self.button_search: QPushButton = QPushButton(self.central_widget)
        self.tabs_frequency: QTabWidget = QTabWidget(self.central_widget)
        self.page_by_range: QWidget = QWidget()
        self.layout_by_range: QFormLayout = QFormLayout(self.page_by_range)
        self.spin_frequency_from: QDoubleSpinBox = QDoubleSpinBox(self.page_by_range)
        self.spin_frequency_to: QDoubleSpinBox = QDoubleSpinBox(self.page_by_range)
        self.page_by_center: QWidget = QWidget()
        self.layout_by_center: QFormLayout = QFormLayout(self.page_by_center)
        self.spin_frequency_center: QDoubleSpinBox = QDoubleSpinBox(self.page_by_center)
        self.spin_frequency_deviation: QDoubleSpinBox = QDoubleSpinBox(self.page_by_center)
        self.menu_bar: QMenuBar = QMenuBar(self)
        self.menu_file: QMenu = QMenu(self.menu_bar.tr('&File'), self.menu_bar)
        self.menu_help: QMenu = QMenu(self.menu_bar.tr('&Help'), self.menu_bar)
        self.menu_edit: QMenu = QMenu(self.menu_bar.tr('&Edit'), self.menu_bar)
        self.menu_columns: QMenu = QMenu(self.menu_bar.tr('&Columns'), self.menu_bar)
        self.menu_copy_only: QMenu = QMenu(self.menu_edit.tr('Copy &Only'), self.menu_edit)
        self.action_load: QAction = QAction(QIcon.fromTheme('document-open'), self.menu_file.tr('&Load Catalog...'),
                                            self.menu_file)
        self.action_preferences: QAction = QAction('&Preferences...', self.menu_file)
        self.action_quit: QAction = QAction(QIcon.fromTheme('application-exit'), self.menu_file.tr('&Quit'),
                                            self.menu_file)
        self.action_about: QAction = QAction(QIcon.fromTheme('help-about'), self.menu_help.tr('&About...'),
                                             self.menu_help)
        self.action_about_qt: QAction = QAction(self.style().standardIcon(QStyle.SP_TitleBarMenuButton),
                                                self.menu_help.tr('About &Qt...'), self.menu_help)
        self.action_copy: QAction = QAction(QIcon.fromTheme('edit-copy'), self.menu_edit.tr('Co&py Selection'),
                                            self.menu_edit)
        self.action_clear: QAction = QAction(QIcon.fromTheme('edit-clear'), self.menu_edit.tr('&Clear Results'),
                                             self.menu_edit)
        self.action_select_all: QAction = QAction(QIcon.fromTheme('edit-select-all'), self.menu_edit.tr('&Select All'),
                                                  self.menu_edit)
        self.action_reload: QAction = QAction(QIcon.fromTheme('document-revert'), self.menu_file.tr('&Reload Catalogs'),
                                              self.menu_file)
        self.action_copy_name: QAction = QAction(self.menu_copy_only.tr('&Substance Name'), self.menu_copy_only)
        self.action_copy_frequency: QAction = QAction(self.menu_copy_only.tr('&Frequency'), self.menu_copy_only)
        self.action_copy_intensity: QAction = QAction(self.menu_copy_only.tr('&Intensity'), self.menu_copy_only)
        self.action_copy_lower_state_energy: QAction = QAction(self.menu_copy_only.tr('&Lower state energy'),
                                                               self.menu_copy_only)
        self.action_show_frequency: QAction = QAction(self.menu_columns.tr('&Frequency'), self.menu_columns)
        self.action_show_intensity: QAction = QAction(self.menu_columns.tr('&Intensity'), self.menu_columns)
        self.action_show_lower_state_energy: QAction = QAction(self.menu_columns.tr('&Lower state energy'),
                                                               self.menu_columns)
        self.action_substance_info: QAction = QAction(self.menu_edit.tr('Substance &Info'), self.menu_edit)
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
            self.setWindowTitle(self.tr('PyQtCatSearch'))
            self.setCentralWidget(self.central_widget)
            self.layout_main.setColumnStretch(0, 1)
            self.layout_main.setRowStretch(4, 1)

            self.results_table.setMouseTracking(True)
            self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.results_table.setDropIndicatorShown(False)
            self.results_table.setDragDropOverwriteMode(False)
            self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.results_table.setCornerButtonEnabled(False)
            self.results_table.setColumnCount(4)
            self.results_table.setRowCount(0)
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
            self.box_substance.setCheckable(True)
            self.box_substance.setTitle(self.box_substance.tr('Search Only For…'))
            self.text_substance.setClearButtonEnabled(True)
            self.text_substance.setPlaceholderText(self.text_substance.tr('Filter'))
            self.layout_substance.addWidget(self.text_substance, 0, 0, 1, 1)
            self.list_substance.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.list_substance.setDropIndicatorShown(False)
            self.list_substance.setAlternatingRowColors(True)
            self.list_substance.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.list_substance.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.list_substance.setSortingEnabled(False)
            self.layout_substance.addWidget(self.list_substance, 1, 0, 1, 1)
            self.check_keep_selection.setStatusTip(
                self.check_keep_selection.tr('Keep substances list selection through filter changes'))
            self.check_keep_selection.setText(self.check_keep_selection.tr('Persistent Selection'))
            self.layout_substance.addWidget(self.check_keep_selection, 2, 0, 1, 1)
            self.button_select_none.setStatusTip(self.button_select_none.tr('Clear substances list selection'))
            self.button_select_none.setText(self.button_select_none.tr('Select None'))
            self.layout_substance.addWidget(self.button_select_none, 3, 0, 1, 1)
            self.layout_main.addWidget(self.box_substance, 0, 0, 4, 1)

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

            self.layout_by_range.setLabelAlignment(Qt.AlignLeft)
            self.spin_frequency_from.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_frequency_from.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_frequency_from.setAccelerated(True)
            self.spin_frequency_from.setDecimals(4)
            self.spin_frequency_from.setMaximum(9999999.9999)
            self.spin_frequency_from.setValue(118747.341)
            self.spin_frequency_from.setSuffix(self.spin_frequency_from.tr(' MHz'))
            self.layout_by_range.addRow(self.layout_by_range.tr('From:'), self.spin_frequency_from)
            self.spin_frequency_to.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_frequency_to.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_frequency_to.setAccelerated(True)
            self.spin_frequency_to.setDecimals(4)
            self.spin_frequency_to.setMaximum(9999999.9999)
            self.spin_frequency_to.setValue(118753.341)
            self.spin_frequency_to.setSuffix(self.spin_frequency_to.tr(' MHz'))
            self.layout_by_range.addRow(self.layout_by_range.tr('To:'), self.spin_frequency_to)
            self.tabs_frequency.addTab(self.page_by_range, self.tabs_frequency.tr('Range'))

            self.spin_frequency_center.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_frequency_center.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_frequency_center.setAccelerated(True)
            self.spin_frequency_center.setDecimals(4)
            self.spin_frequency_center.setMaximum(9999999.9999)
            self.spin_frequency_center.setValue(118750.341)
            self.spin_frequency_center.setSuffix(self.spin_frequency_center.tr(' MHz'))
            self.layout_by_center.addRow(self.layout_by_center.tr('Center:'), self.spin_frequency_center)
            self.spin_frequency_deviation.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
            self.spin_frequency_deviation.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self.spin_frequency_deviation.setDecimals(4)
            self.spin_frequency_deviation.setMaximum(99.9999)
            self.spin_frequency_deviation.setSingleStep(0.1)
            self.spin_frequency_deviation.setValue(0.4)
            self.spin_frequency_deviation.setSuffix(self.spin_frequency_deviation.tr(' MHz'))
            self.layout_by_center.addRow(self.layout_by_center.tr('Deviation:'), self.spin_frequency_deviation)
            self.tabs_frequency.addTab(self.page_by_center, self.tabs_frequency.tr('Center'))
            self.layout_main.addWidget(self.tabs_frequency, 0, 1, 2, 1)

            self.setMenuBar(self.menu_bar)
            self.action_preferences.setMenuRole(QAction.PreferencesRole)
            self.action_quit.setMenuRole(QAction.QuitRole)
            self.action_about.setMenuRole(QAction.AboutRole)
            self.action_about_qt.setMenuRole(QAction.AboutQtRole)
            self.menu_file.addAction(self.action_load)
            self.menu_file.addAction(self.action_reload)
            self.menu_file.addSeparator()
            self.menu_file.addAction(self.action_preferences)
            self.menu_file.addSeparator()
            self.menu_file.addAction(self.action_quit)
            self.menu_help.addAction(self.action_about)
            self.menu_help.addAction(self.action_about_qt)
            self.menu_copy_only.addAction(self.action_copy_name)
            self.menu_copy_only.addAction(self.action_copy_frequency)
            self.menu_copy_only.addAction(self.action_copy_intensity)
            self.menu_copy_only.addAction(self.action_copy_lower_state_energy)
            self.menu_edit.addAction(self.action_clear)
            self.menu_edit.addSeparator()
            self.menu_edit.addAction(self.menu_copy_only.menuAction())
            self.menu_edit.addAction(self.action_copy)
            self.menu_edit.addSeparator()
            self.menu_edit.addAction(self.action_select_all)
            self.menu_edit.addSeparator()
            self.menu_edit.addAction(self.action_substance_info)
            self.menu_columns.addAction(self.action_show_frequency)
            self.menu_columns.addAction(self.action_show_intensity)
            self.menu_columns.addAction(self.action_show_lower_state_energy)
            self.menu_bar.addAction(self.menu_file.menuAction())
            self.menu_bar.addAction(self.menu_edit.menuAction())
            self.menu_bar.addAction(self.menu_columns.menuAction())
            self.menu_bar.addAction(self.menu_help.menuAction())
            self.setStatusBar(self.status_bar)

            self.button_search.setShortcut('Ctrl+Return')
            self.action_load.setShortcut('Ctrl+L')
            self.action_quit.setShortcut('Ctrl+Q')
            self.action_about.setShortcut('F1')
            self.action_preferences.setShortcut('Ctrl+,')
            self.action_copy.setShortcut('Ctrl+C')
            self.action_select_all.setShortcut('Ctrl+A')
            self.action_reload.setShortcut('Ctrl+R')
            self.action_copy_name.setShortcut('Ctrl+Shift+C, N')
            self.action_copy_frequency.setShortcut('Ctrl+Shift+C, F')
            self.action_copy_intensity.setShortcut('Ctrl+Shift+C, I')
            self.action_copy_lower_state_energy.setShortcut('Ctrl+Shift+C, E')
            self.action_substance_info.setShortcut('Ctrl+I')
            self.action_show_frequency.setCheckable(True)
            self.action_show_intensity.setCheckable(True)
            self.action_show_lower_state_energy.setCheckable(True)

            self.adjustSize()

        setup_ui()

        self.frequency_from: float = -math.inf  # [MHz]
        self.frequency_to: float = math.inf  # [MHz]
        self.frequency_center: float = 0  # [MHz]
        self.frequency_deviation: float = math.inf  # [MHz]
        self.temperature: float = 300.0  # [K]
        self.minimal_intensity: float = -math.inf  # [log10(nm²×MHz)]

        self.catalog: Catalog = catalog
        self.button_search.setDisabled(self.catalog.is_empty)
        self.selected_substances: Set[str] = set()

        self.settings: Settings = Settings('SavSoft', 'CatSearch', self)
        self.preferences_dialog: Preferences = Preferences(self.settings, self)

        self.results_shown: bool = False

        self.preset_table()

        self.load_settings()

        self.results_table.customContextMenuRequested.connect(self.on_table_context_menu_requested)
        self.results_table.itemSelectionChanged.connect(self.on_table_item_selection_changed)
        self.results_table.cellDoubleClicked.connect(self.on_action_substance_info_triggered)
        self.text_substance.textChanged.connect(self.text_substance_changed)
        self.check_keep_selection.toggled.connect(self.on_check_save_selection_toggled)
        self.button_select_none.clicked.connect(self.on_button_select_none_clicked)
        self.spin_intensity.valueChanged.connect(self.on_spin_intensity_changed)
        self.spin_temperature.valueChanged.connect(self.on_spin_temperature_changed)
        self.button_search.clicked.connect(self.on_button_search_clicked)
        self.spin_frequency_from.editingFinished.connect(self.on_spin_frequency_from_edited)
        self.spin_frequency_to.editingFinished.connect(self.on_spin_frequency_to_edited)
        self.spin_frequency_center.editingFinished.connect(self.on_spin_frequency_center_edited)
        self.spin_frequency_deviation.editingFinished.connect(self.on_spin_frequency_deviation_edited)
        self.action_load.triggered.connect(self.on_action_load_triggered)
        self.action_quit.triggered.connect(self.on_action_quit_triggered)
        self.action_about.triggered.connect(self.on_action_about_triggered)
        self.action_about_qt.triggered.connect(self.on_action_about_qt_triggered)
        self.action_preferences.triggered.connect(self.on_action_preferences_triggered)
        self.action_copy.triggered.connect(self.on_action_copy_triggered)
        self.action_select_all.triggered.connect(self.on_action_select_all_triggered)
        self.action_reload.triggered.connect(self.on_action_reload_triggered)
        self.action_copy_name.triggered.connect(self.on_action_copy_name_triggered)
        self.action_copy_frequency.triggered.connect(self.on_action_copy_frequency_triggered)
        self.action_copy_intensity.triggered.connect(self.on_action_copy_intensity_triggered)
        self.action_copy_lower_state_energy.triggered.connect(self.on_action_copy_lower_state_energy_triggered)
        self.action_show_frequency.toggled.connect(self.on_action_show_frequency_toggled)
        self.action_show_intensity.toggled.connect(self.on_action_show_intensity_toggled)
        self.action_show_lower_state_energy.toggled.connect(self.on_action_show_lower_state_energy_toggled)
        self.action_substance_info.triggered.connect(self.on_action_substance_info_triggered)
        self.action_clear.triggered.connect(self.on_action_clear_triggered)

        if not self.catalog.is_empty:
            frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                     self.spin_frequency_center]
            for spin in frequency_spins:
                spin.setMinimum(self.settings.from_mhz(self.catalog.min_frequency))
                spin.setMaximum(self.settings.from_mhz(self.catalog.max_frequency))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def on_spin_frequency_from_edited(self):
        self.frequency_from = \
            self.settings.to_mhz(self.spin_frequency_from.value())

    def on_spin_frequency_to_edited(self):
        self.frequency_to = \
            self.settings.to_mhz(self.spin_frequency_to.value())

    def on_spin_frequency_center_edited(self):
        self.frequency_center = \
            self.settings.to_mhz(self.spin_frequency_center.value())

    def on_spin_frequency_deviation_edited(self):
        self.frequency_deviation = \
            self.settings.to_mhz(self.spin_frequency_deviation.value())

    def text_substance_changed(self, current_text: str):
        self.fill_substances_list(current_text)

    def on_spin_temperature_changed(self, arg1: float):
        self.temperature = self.settings.to_k(arg1)
        self.fill_table()

    def on_spin_intensity_changed(self, arg1: float):
        self.minimal_intensity = self.settings.to_log10_sq_nm_mhz(arg1)
        if self.results_shown:
            self.fill_table()

    def on_check_save_selection_toggled(self, new_state):
        if not new_state:
            self.selected_substances.clear()
            self.update_selected_substances()

    def on_button_select_none_clicked(self):
        for i in range(self.list_substance.count()):
            self.list_substance.item(i).setCheckState(Qt.Unchecked)
        self.selected_substances.clear()

    def on_table_context_menu_requested(self, pos: QPoint):
        self.menu_edit.popup(self.results_table.viewport().mapToGlobal(pos))

    def on_table_item_selection_changed(self):
        self.action_copy.setEnabled(bool(self.results_table.selectedItems()))
        self.action_substance_info.setEnabled(bool(self.results_table.selectedItems()))
        for r in range(self.results_table.rowCount()):
            # noinspection PyTypeChecker
            label: Optional[QLabel] = self.results_table.cellWidget(r, 0)
            if label is not None:
                if self.results_table.item(r, 1).isSelected():
                    label.setSelection(0, len(remove_html(label.text())))
                else:
                    label.setSelection(0, 0)

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
            self.button_search.setDisabled(self.catalog.is_empty)
            if not self.catalog.is_empty:
                self.status_bar.showMessage(self.tr('Catalogs loaded.'))
                frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                         self.spin_frequency_center]
                for spin in frequency_spins:
                    spin.setMinimum(self.settings.from_mhz(self.catalog.min_frequency))
                    spin.setMaximum(self.settings.from_mhz(self.catalog.max_frequency))
                self.fill_substances_list(self.text_substance.text())
            else:
                self.status_bar.showMessage(self.tr('Failed to load a catalog.'))

        else:
            self.status_bar.clearMessage()

    def on_action_reload_triggered(self):
        if self.catalog.sources:
            self.status_bar.showMessage(self.tr('Loading...'))
            self.catalog = Catalog(*self.catalog.sources)
            self.button_search.setDisabled(self.catalog.is_empty)
            if not self.catalog.is_empty:
                self.status_bar.showMessage(self.tr('Catalogs loaded.'))
                frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                         self.spin_frequency_center]
                for spin in frequency_spins:
                    spin.setMinimum(self.settings.from_mhz(self.catalog.min_frequency))
                    spin.setMaximum(self.settings.from_mhz(self.catalog.max_frequency))
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
        selection: QTableWidgetSelectionRange
        if self.settings.with_units:
            units: Dict[int, str] = {
                1: self.settings.frequency_unit_str,
                2: self.settings.intensity_unit_str
            }
            for selection in self.results_table.selectedRanges():
                for r in range(selection.topRow(), selection.bottomRow() + 1):
                    text.append(
                        '<tr><td>' +
                        f'</td>{self.settings.csv_separator}<td>'.join(
                            [self.results_table.cellWidget(r, 0).text()] +
                            [(self.results_table.item(r, _c).text() + (' ' + units[_c] if _c in units else ''))
                             for _c, _a in zip(range(1, self.results_table.columnCount()), self.menu_columns.actions())
                             if _a.isChecked()]
                        ) +
                        '</td></tr>' + self.settings.line_end
                    )
        else:
            for selection in self.results_table.selectedRanges():
                for r in range(selection.topRow(), selection.bottomRow() + 1):
                    text.append(
                        '<tr><td>' +
                        f'</td>{self.settings.csv_separator}<td>'.join(
                            [self.results_table.cellWidget(r, 0).text()] +
                            [self.results_table.item(r, _c).text()
                             for _c, _a in zip(range(1, self.results_table.columnCount()), self.menu_columns.actions())
                             if _a.isChecked()]
                        ) +
                        '</td></tr>' + self.settings.line_end
                    )
        return '<table>' + self.settings.line_end + ''.join(text) + '</table>'

    def on_action_preferences_triggered(self):
        self.preferences_dialog.exec()
        self.fill_parameters()
        if self.results_table.rowCount():
            self.preset_table()
            self.fill_table()
        else:
            self.preset_table()

    def on_action_quit_triggered(self):
        self.close()

    def on_action_clear_triggered(self):
        self.preset_table()

    def copy_selected_items(self, col: int):
        if col >= self.results_table.columnCount():
            return

        def html_list(lines: List[str]) -> str:
            return '<ul><li>' + f'</li>{self.settings.line_end}<li>'.join(lines) + '</li></ul>'

        text_to_copy: List[str] = []
        selection: QTableWidgetSelectionRange
        if col == 0:
            for selection in self.results_table.selectedRanges():
                for row in range(selection.topRow(), selection.bottomRow() + 1):
                    text_to_copy.append(self.results_table.cellWidget(row, col).text())
            copy_to_clipboard(html_list(text_to_copy), Qt.RichText)
        else:
            for selection in self.results_table.selectedRanges():
                for row in range(selection.topRow(), selection.bottomRow() + 1):
                    text_to_copy.append(self.results_table.item(row, col).text())
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
        if self.results_table.selectedRanges():
            syn: SubstanceInfo = SubstanceInfo(
                self.catalog,
                getattr(self.results_table.cellWidget(self.results_table.selectedRanges()[0].topRow(), 0), ID),
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
        self.settings.beginGroup('selection')
        self.text_substance.setText(self.settings.value('filter', self.text_substance.text(), str))
        self.check_keep_selection.setChecked(self.settings.value('isPersistent', False, bool))
        self.box_substance.setChecked(self.settings.value('enabled', self.box_substance.isChecked(), bool))
        self.settings.endGroup()
        self.temperature = self.settings.value('temperature', self.spin_temperature.value(), float)
        self.minimal_intensity = self.settings.value('intensity', self.spin_intensity.value(), float)
        self.settings.beginGroup('frequency')
        self.frequency_from = self.settings.value('from', self.spin_frequency_from.value(), float)
        self.frequency_to = self.settings.value('to', self.spin_frequency_to.value(), float)
        self.frequency_center = self.settings.value('center', self.spin_frequency_center.value(), float)
        self.frequency_deviation = self.settings.value('deviation', self.spin_frequency_deviation.value(), float)
        self.settings.endGroup()
        self.settings.endGroup()
        self.settings.beginGroup('displayedColumns')
        self.action_show_frequency.setChecked(self.settings.value('frequency', True, bool))
        self.toggle_results_table_column_visibility(1, self.action_show_frequency.isChecked())
        self.action_show_intensity.setChecked(self.settings.value('intensity', True, bool))
        self.toggle_results_table_column_visibility(2, self.action_show_intensity.isChecked())
        self.action_show_lower_state_energy.setChecked(self.settings.value('lowerStateEnergy', False, bool))
        self.toggle_results_table_column_visibility(3, self.action_show_lower_state_energy.isChecked())
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
                frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                         self.spin_frequency_center]
                for spin in frequency_spins:
                    spin.setMinimum(self.settings.from_mhz(self.catalog.min_frequency))
                    spin.setMaximum(self.settings.from_mhz(self.catalog.max_frequency))
                self.fill_substances_list(self.text_substance.text())

    def save_settings(self):
        self.settings.beginGroup('search')
        self.settings.beginWriteArray('catalogFiles', len(self.catalog.sources))
        for i, s in enumerate(self.catalog.sources):
            self.settings.setArrayIndex(i)
            self.settings.setValue('path', s)
        self.settings.endArray()
        self.settings.beginGroup('selection')
        self.settings.setValue('filter', self.text_substance.text())
        self.settings.setValue('isPersistent', self.check_keep_selection.isChecked())
        self.settings.setValue('enabled', self.box_substance.isChecked())
        self.settings.endGroup()
        self.settings.setValue('temperature', self.temperature)
        self.settings.setValue('intensity', self.minimal_intensity)
        self.settings.beginGroup('frequency')
        self.settings.setValue('from', self.frequency_from)
        self.settings.setValue('to', self.frequency_to)
        self.settings.setValue('center', self.frequency_center)
        self.settings.setValue('deviation', self.frequency_deviation)
        self.settings.endGroup()
        self.settings.endGroup()
        self.settings.beginGroup('displayedColumns')
        self.settings.setValue('frequency', self.action_show_frequency.isChecked())
        self.settings.setValue('intensity', self.action_show_intensity.isChecked())
        self.settings.setValue('lowerStateEnergy', self.action_show_lower_state_energy.isChecked())
        self.settings.endGroup()
        self.settings.beginGroup('window')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('state', self.saveState())
        self.settings.endGroup()
        self.settings.sync()

    def preset_table(self):
        self.results_shown = False
        self.results_table.clearContents()
        self.results_table.clearSelection()
        self.action_copy.setDisabled(True)
        self.action_substance_info.setDisabled(True)
        self.action_select_all.setDisabled(True)
        self.action_clear.setDisabled(True)
        self.menu_copy_only.setDisabled(True)
        self.results_table.setRowCount(0)
        self.results_table.setHorizontalHeaderLabels(
            [
                self.tr('Substance'),
                f'{self.tr("Frequency")} [{self.settings.frequency_unit_str}]',
                f'{self.tr("Intensity")} [{self.settings.intensity_unit_str}]',
                f'{self.tr("Lower state energy")} [{self.settings.energy_unit_str}]',
            ]
        )
        self.update()

    def fill_parameters(self):
        # frequency
        frequency_suffix: int = self.settings.frequency_unit
        frequency_suffix_str: str = ' ' + self.settings.FREQUENCY_UNITS[frequency_suffix]
        if not self.catalog.is_empty:
            frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                     self.spin_frequency_center]
            for spin in frequency_spins:
                spin.setMinimum(self.settings.from_mhz(self.catalog.min_frequency))
                spin.setMaximum(self.settings.from_mhz(self.catalog.max_frequency))
        if frequency_suffix in (0, 1, 2):  # MHz, GHz, cm⁻¹
            self.spin_frequency_from.setValue(self.settings.from_mhz(self.frequency_from))
            self.spin_frequency_to.setValue(self.settings.from_mhz(self.frequency_to))
            self.spin_frequency_center.setValue(self.settings.from_mhz(self.frequency_center))
            self.spin_frequency_deviation.setValue(self.settings.from_mhz(self.frequency_deviation))
        elif frequency_suffix == 3:  # nm
            self.spin_frequency_from.setValue(mhz_to_nm(self.frequency_from))
            self.spin_frequency_to.setValue(mhz_to_nm(self.frequency_to))
            self.spin_frequency_center.setValue(mhz_to_nm(self.frequency_center))
            self.spin_frequency_deviation.setValue(
                abs(mhz_to_nm(self.frequency_center - self.frequency_deviation) -
                    mhz_to_nm(self.frequency_center + self.frequency_deviation)) / 2.0)
        else:
            raise IndexError('Wrong frequency unit index', frequency_suffix)
        precision: int = [4, 7, 8, 8][frequency_suffix]
        step_factor: float = [2.5, 2.5, 2.5, 0.25][frequency_suffix]
        frequency_spins: List[QDoubleSpinBox] = [self.spin_frequency_from, self.spin_frequency_to,
                                                 self.spin_frequency_center, self.spin_frequency_deviation]
        for spin in frequency_spins:
            spin.setSuffix(frequency_suffix_str)
            spin.setDecimals(precision)
            spin.setSingleStep(step_factor * self.spin_frequency_deviation.value())

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

        min_frequency: float = (self.frequency_from
                                if self.tabs_frequency.currentWidget() is self.page_by_range
                                else (self.frequency_center - self.frequency_deviation))
        max_frequency: float = (self.frequency_to
                                if self.tabs_frequency.currentWidget() is self.page_by_range
                                else (self.frequency_center + self.frequency_deviation))
        entries: List[Dict[str, Union[int, str, List[Dict[str, float]]]]] = \
            (sum(
                (
                    self.catalog.filter(min_frequency=min_frequency,
                                        max_frequency=max_frequency,
                                        min_intensity=self.minimal_intensity,
                                        any_name_or_formula=name,
                                        temperature=self.temperature)
                    for name in self.selected_substances
                ),
                []
            ) if self.selected_substances and self.box_substance.isChecked()
             else self.catalog.filter(min_frequency=min_frequency,
                                      max_frequency=max_frequency,
                                      min_intensity=self.minimal_intensity,
                                      temperature=self.temperature))
        frequency_suffix: int = self.settings.frequency_unit
        precision: int = [4, 7, 8, 8][frequency_suffix]
        if len(entries) > self.MAX_ENTRIES_COUNT:
            entries = entries[:self.MAX_ENTRIES_COUNT]
            QMessageBox.warning(self,
                                self.tr('Too many results'),
                                self.tr('There are too many lines that meet your criteria. '
                                        'Not all of them are displayed.'))
        for entry in entries:
            for line in entry[LINES]:
                last_row: int = self.results_table.rowCount()
                self.results_table.setRowCount(last_row + 1)

                label: QLabel = QLabel(best_name(entry, self.settings.rich_text_in_formulas), self.results_table)
                label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                setattr(label, ID, entry[ID])
                p: QPalette = QPalette(self.results_table.palette())
                p.setBrush(QPalette.Inactive, QPalette.Highlight, p.highlight())
                p.setBrush(QPalette.Inactive, QPalette.HighlightedText, p.highlightedText())
                label.setPalette(p)
                self.results_table.setCellWidget(last_row, 0, label)

                frequency: float = self.settings.from_mhz(line[FREQUENCY])
                item: QTableWidgetItem = QTableWidgetItem(f'{frequency:.{precision}f}')
                item.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
                self.results_table.setItem(last_row, 1, item)

                intensity: float = self.settings.from_log10_sq_nm_mhz(line[INTENSITY])
                if intensity == 0.0:
                    item: QTableWidgetItem = QTableWidgetItem('0')
                elif abs(intensity) < 0.1:
                    item: QTableWidgetItem = QTableWidgetItem(f'{intensity:.4e}')
                else:
                    item: QTableWidgetItem = QTableWidgetItem(f'{intensity:.4f}')
                item.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
                self.results_table.setItem(last_row, 2, item)

                lower_state_energy: float = self.settings.from_rec_cm(line[LOWER_STATE_ENERGY])
                if lower_state_energy == 0.0:
                    item: QTableWidgetItem = QTableWidgetItem('0')
                elif abs(lower_state_energy) < 0.1:
                    item: QTableWidgetItem = QTableWidgetItem(f'{lower_state_energy:.4e}')
                else:
                    item: QTableWidgetItem = QTableWidgetItem(f'{lower_state_energy:.4f}')
                item.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
                self.results_table.setItem(last_row, 3, item)

        self.results_table.setSortingEnabled(True)
        self.action_select_all.setEnabled(bool(entries))
        self.action_clear.setEnabled(bool(entries))
        self.menu_copy_only.setEnabled(bool(entries))
        self.results_shown = True

    def update_selected_substances(self):
        if self.box_substance.isChecked():
            for i in range(self.list_substance.count()):
                item: QListWidgetItem = self.list_substance.item(i)
                if item.checkState() == Qt.Checked:
                    self.selected_substances.add(item.text())
                else:
                    self.selected_substances.discard(item.text())
        else:
            self.selected_substances.clear()

    def filter_substances_list(self, filter_text: str) -> List[str]:
        list_items: List[str] = []
        if filter_text:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self.catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if (name_key in entry and plain_text_name.startswith(filter_text)
                            and plain_text_name not in list_items):
                        list_items.append(plain_text_name)
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self.catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if name_key in entry and filter_text in plain_text_name and plain_text_name not in list_items:
                        list_items.append(plain_text_name)
            if filter_text.isdecimal():
                for entry in self.catalog.catalog:
                    if SPECIES_TAG in entry and str(entry[SPECIES_TAG]).startswith(filter_text):
                        list_items.append(str(entry[SPECIES_TAG]))
        else:
            for name_key in (ISOTOPOLOG, NAME, STRUCTURAL_FORMULA,
                             STOICHIOMETRIC_FORMULA, TRIVIAL_NAME):
                for entry in self.catalog.catalog:
                    plain_text_name: str = remove_html(entry[name_key])
                    if plain_text_name not in list_items:
                        list_items.append(plain_text_name)
            list_items = sorted(list_items)
        return list_items

    def fill_substances_list(self, filter_text: str):
        self.update_selected_substances()
        self.list_substance.clear()

        for text in self.filter_substances_list(filter_text):
            new_item: QListWidgetItem = QListWidgetItem(text, self.list_substance)
            new_item.setFlags(int(new_item.flags()) | Qt.ItemIsUserCheckable)
            new_item.setCheckState(Qt.Checked if text in self.selected_substances else Qt.Unchecked)
            self.list_substance.addItem(new_item)

    def on_button_search_clicked(self):
        self.status_bar.showMessage(self.tr('Searching...'))
        self.update_selected_substances()
        self.fill_table()
        self.status_bar.showMessage(self.tr('Ready.'))


def run():
    app = QApplication(sys.argv)
    window = UI(Catalog(*sys.argv[1:]))
    window.show()
    app.exec_()


if __name__ == '__main__':
    run()
