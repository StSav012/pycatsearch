# -*- coding: utf-8 -*-
from typing import Type

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QMenuBar, \
    QStyle

class MenuBar(QMenuBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menu_file: QMenu = QMenu(self.tr('&File'), self)
        self.menu_help: QMenu = QMenu(self.tr('&Help'), self)
        self.menu_edit: QMenu = QMenu(self.tr('&Edit'), self)
        self.menu_columns: QMenu = QMenu(self.tr('&Columns'), self)
        self.menu_copy_only: QMenu = QMenu(self.tr('Copy &Only'), self.menu_edit)
        self.action_load: QAction = QAction(QIcon.fromTheme('document-open'), self.tr('&Load Catalog...'),
                                            self.menu_file)
        self.action_preferences: QAction = QAction('&Preferences...', self.menu_file)
        self.action_quit: QAction = QAction(QIcon.fromTheme('application-exit'), self.tr('&Quit'),
                                            self.menu_file)
        self.action_about: QAction = QAction(QIcon.fromTheme('help-about'), self.tr('&About...'),
                                             self.menu_help)
        self.action_about_qt: QAction = QAction(self.style().standardIcon(QStyle.SP_TitleBarMenuButton),
                                                self.tr('About &Qt...'), self.menu_help)
        self.action_copy: QAction = QAction(QIcon.fromTheme('edit-copy'), self.tr('Co&py Selection'),
                                            self.menu_edit)
        self.action_clear: QAction = QAction(QIcon.fromTheme('edit-clear'), self.tr('&Clear Results'),
                                             self.menu_edit)
        self.action_select_all: QAction = QAction(QIcon.fromTheme('edit-select-all'), self.tr('&Select All'),
                                                  self.menu_edit)
        self.action_reload: QAction = QAction(QIcon.fromTheme('document-revert'), self.tr('&Reload Catalogs'),
                                              self.menu_file)
        self.action_copy_name: QAction = QAction(self.tr('&Substance Name'), self.menu_copy_only)
        self.action_copy_frequency: QAction = QAction(self.tr('&Frequency'), self.menu_copy_only)
        self.action_copy_intensity: QAction = QAction(self.tr('&Intensity'), self.menu_copy_only)
        self.action_copy_lower_state_energy: QAction = QAction(self.menu_copy_only.tr('&Lower state energy'),
                                                               self.menu_copy_only)
        self.action_show_frequency: QAction = QAction(self.tr('&Frequency'), self.menu_columns)
        self.action_show_intensity: QAction = QAction(self.tr('&Intensity'), self.menu_columns)
        self.action_show_lower_state_energy: QAction = QAction(self.tr('&Lower state energy'),
                                                               self.menu_columns)
        self.action_substance_info: QAction = QAction(self.tr('Substance &Info'), self.menu_edit)

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
        self.addAction(self.menu_file.menuAction())
        self.addAction(self.menu_edit.menuAction())
        self.addAction(self.menu_columns.menuAction())
        self.addAction(self.menu_help.menuAction())

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
