# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import suppress
from typing import Any

from qtpy.QtGui import QIcon, QKeySequence
from qtpy.QtWidgets import QAction, QMenu, QMenuBar, QStyle, QWidget

__all__ = ["MenuBar"]


class MenuBar(QMenuBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.menu_file: QMenu = self.addMenu(self.tr("&File"))
        self.action_load: QAction = self.menu_file.addAction(
            self._icon("document-open", "mdi6.folder-open", standard_pixmap=QStyle.StandardPixmap.SP_DialogOpenButton),
            self.tr("&Load Catalog…"),
            QKeySequence.StandardKey.Open,
        )
        self.action_reload: QAction = self.menu_file.addAction(
            self._icon("document-revert", "mdi6.reload", standard_pixmap=QStyle.StandardPixmap.SP_BrowserReload),
            self.tr("&Reload Catalogs"),
            QKeySequence.StandardKey.Refresh,
        )
        self.action_save_as: QAction = self.menu_file.addAction(
            self._icon(
                "document-save-as", "mdi6.content-save-edit", standard_pixmap=QStyle.StandardPixmap.SP_DialogSaveButton
            ),
            self.tr("&Save Catalog As…"),
            QKeySequence.StandardKey.SaveAs,
        )
        self.menu_file.addSeparator()
        self.action_download_catalog: QAction = self.menu_file.addAction(
            self._icon("network-receive", "mdi6.download"), self.tr("&Download Catalog…")
        )
        self.menu_file.addSeparator()
        self.action_preferences: QAction = self.menu_file.addAction(
            self._icon("preferences-other", "mdi6.application-settings"),
            self.tr("&Preferences…"),
            QKeySequence.StandardKey.Preferences,
        )
        self.menu_file.addSeparator()
        self.action_quit: QAction = self.menu_file.addAction(
            self._icon("application-exit", "mdi6.exit-run", standard_pixmap=QStyle.StandardPixmap.SP_DialogCloseButton),
            self.tr("&Quit"),
            QKeySequence.StandardKey.Quit,
        )

        self.menu_edit: QMenu = self.addMenu(self.tr("&Edit"))
        self.action_clear: QAction = self.menu_edit.addAction(
            self._icon("edit-clear", "mdi6.broom", standard_pixmap=QStyle.StandardPixmap.SP_DialogResetButton),
            self.tr("Clea&r Results"),
        )
        self.menu_edit.addSeparator()
        self.menu_copy_only: QMenu = self.menu_edit.addMenu(self.tr("Copy &Only"))
        self.action_copy_current: QAction = self.menu_copy_only.addAction(self.tr("Active &Cell"), "Ctrl+Shift+C")
        self.menu_copy_only.addSeparator()
        self.action_copy_name: QAction = self.menu_copy_only.addAction(self.tr("&Substance Name"), "Ctrl+Shift+C, N")
        self.action_copy_frequency: QAction = self.menu_copy_only.addAction(self.tr("&Frequency"), "Ctrl+Shift+C, F")
        self.action_copy_intensity: QAction = self.menu_copy_only.addAction(self.tr("&Intensity"), "Ctrl+Shift+C, I")
        self.action_copy_lower_state_energy: QAction = self.menu_copy_only.addAction(
            self.tr("&Lower State Energy"), "Ctrl+Shift+C, E"
        )
        self.action_copy: QAction = self.menu_edit.addAction(
            self._icon("edit-copy", "mdi6.content-copy"), self.tr("&Copy Selection"), QKeySequence.StandardKey.Copy
        )
        self.menu_edit.addSeparator()
        self.action_select_all: QAction = self.menu_edit.addAction(
            self._icon("edit-select-all", "mdi6.select-all"), self.tr("Select &All"), QKeySequence.StandardKey.SelectAll
        )
        self.menu_edit.addSeparator()
        self.action_substance_info: QAction = self.menu_edit.addAction(
            self._icon(
                "dialog-information",
                "mdi6.flask-empty-outline",
                "mdi6.information-variant",
                options=[{}, {"scale_factor": 0.5}],
            ),
            self.tr("Substance &Info"),
            "Ctrl+I",
        )

        self.menu_columns: QMenu = self.addMenu(self.tr("&Columns"))
        self.action_show_substance: QAction = self.menu_columns.addAction(self.tr("&Substance"))
        self.action_show_frequency: QAction = self.menu_columns.addAction(self.tr("&Frequency"))
        self.action_show_intensity: QAction = self.menu_columns.addAction(self.tr("&Intensity"))
        self.action_show_lower_state_energy: QAction = self.menu_columns.addAction(self.tr("&Lower State Energy"))

        self.menu_help: QMenu = self.addMenu(self.tr("&Help"))
        self.action_check_updates: QAction = self.menu_help.addAction(
            self._icon("application-update", "mdi6.update"), self.tr("Check for &Updates…")
        )
        self.menu_help.addSeparator()
        self.action_about_catalogs: QAction = self.menu_help.addAction(
            self._icon("document-properties", "mdi6.information"), self.tr("About &Catalogs…")
        )
        self.action_about: QAction = self.menu_help.addAction(
            self._icon("help-about", "mdi6.help", standard_pixmap=QStyle.StandardPixmap.SP_FileDialogInfoView),
            self.tr("&About…"),
            QKeySequence.StandardKey.HelpContents,
        )
        self.action_about_qt: QAction = self.menu_help.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMenuButton), self.tr("About &Qt…")
        )

        self.action_preferences.setMenuRole(QAction.MenuRole.PreferencesRole)
        self.action_quit.setMenuRole(QAction.MenuRole.QuitRole)
        self.action_about.setMenuRole(QAction.MenuRole.AboutRole)
        self.action_about_qt.setMenuRole(QAction.MenuRole.AboutQtRole)

        self.action_save_as.setDisabled(True)

        self.action_show_substance.setCheckable(True)
        self.action_show_frequency.setCheckable(True)
        self.action_show_intensity.setCheckable(True)
        self.action_show_lower_state_energy.setCheckable(True)

    def _icon(
        self, theme_name: str, *qta_name: str, standard_pixmap: QStyle.StandardPixmap | None = None, **qta_specs: Any
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
