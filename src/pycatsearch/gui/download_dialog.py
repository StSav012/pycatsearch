# -*- coding: utf-8 -*-
from __future__ import annotations

from math import inf

from qtpy.QtWidgets import QDialog, QWidget

from .catalog_wizard import SaveCatalogWizard
from .catalog_wizard.download_confirmation_page import DownloadConfirmationPage
from .catalog_wizard.progress_page import ProgressPage
from .catalog_wizard.settings_page import SettingsPage
from .catalog_wizard.summary_page import SummaryPage
from .settings import Settings

__all__ = ["DownloadDialog"]


class DownloadDialog(SaveCatalogWizard):
    """GUI for `async_downloader.Downloader` or `downloader.Downloader`"""

    def __init__(
        self,
        settings: Settings,
        frequency_limits: tuple[float, float] = (-inf, inf),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(settings=settings, parent=parent)

        self.setWindowTitle(self.tr("Download Catalog"))

        self._settings_page: SettingsPage = SettingsPage(self)
        self.addPage(self._settings_page)
        self.addPage(DownloadConfirmationPage(self))
        self._progress_page: ProgressPage = ProgressPage(self)
        self.addPage(self._progress_page)
        self.addPage(SummaryPage(self))

        self._settings_page.frequency_limits = frequency_limits

    def back(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().back()

    def next(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().next()

    def restart(self) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        super().restart()

    def frequency_limits(self) -> tuple[float, float]:
        return self._settings_page.frequency_limits

    def done(self, exit_code: QDialog.DialogCode) -> None:
        if self._progress_page.isActive():
            self._progress_page.stop()
        return super().done(exit_code)
